// SPDX-License-Identifier: MIT
/**
 * Bounty Browser — sidebar tree view showing open RustChain bounties.
 *
 * Issues are fetched from the GitHub REST API and filtered to those
 * labelled "bounty" (case-insensitive). Clicking an issue opens it
 * in the browser. The "Claim Bounty" quick-action pre-fills a PR
 * template URL for the selected issue.
 */

import * as vscode from "vscode";
import * as https from "https";

const REPO_OWNER = "Scottcjn";
const REPO_NAME = "rustchain-bounties";
const GITHUB_API = "api.github.com";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface GithubIssue {
    number: number;
    title: string;
    html_url: string;
    labels: Array<{ name: string; color: string }>;
    state: string;
    created_at: string;
    body: string | null;
}

// ---------------------------------------------------------------------------
// GitHub API helper
// ---------------------------------------------------------------------------

function ghApiGet<T>(path: string): Promise<T> {
    return new Promise((resolve, reject) => {
        const opts: https.RequestOptions = {
            hostname: GITHUB_API,
            path: `/repos/${REPO_OWNER}/${REPO_NAME}${path}`,
            method: "GET",
            headers: {
                "User-Agent": "rustchain-dev-vscode",
                Accept: "application/vnd.github.v3+json",
            },
        };

        const req = https.get(opts, (res) => {
            if (res.statusCode && (res.statusCode < 200 || res.statusCode >= 300)) {
                reject(new Error(`GitHub API HTTP ${res.statusCode}`));
                return;
            }
            const chunks: Buffer[] = [];
            res.on("data", (c: Buffer) => chunks.push(c));
            res.on("end", () => {
                try {
                    resolve(JSON.parse(Buffer.concat(chunks).toString("utf-8")) as T);
                } catch {
                    reject(new Error("Failed to parse GitHub API response"));
                }
            });
        });

        req.on("error", reject);
        req.setTimeout(10_000, () => {
            req.destroy();
            reject(new Error("GitHub API request timed out"));
        });
    });
}

// ---------------------------------------------------------------------------
// Tree data provider
// ---------------------------------------------------------------------------

type TreeIssue = GithubIssue;

class BountyTreeDataProvider implements vscode.TreeDataProvider<TreeIssue | null> {
    issues: TreeIssue[] = [];
    private _onDidChangeTreeData = new vscode.EventEmitter<TreeIssue | null>();
    readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

    async refresh(): Promise<void> {
        try {
            // Fetch open issues, up to 100, page 1
            const data = await ghApiGet<GithubIssue[]>(
                "/issues?state=open&per_page=100&sort=updated",
            );
            // Filter to bounty-labelled issues
            this.issues = data.filter((issue) =>
                issue.labels.some((l) =>
                    l.name.toLowerCase().includes("bounty"),
                ),
            );
        } catch {
            this.issues = [];
        }
        this._onDidChangeTreeData.fire(null);
    }

    getTreeItem(element: TreeIssue): vscode.TreeItem {
        const item = new vscode.TreeItem(
            element.title,
            vscode.TreeItemCollapsibleState.None,
        );
        item.label = element.title;
        item.tooltip = `(#${element.number}) ${element.title}\n${element.html_url}`;
        item.resourceUri = vscode.Uri.parse(element.html_url);

        const bountyLabel = element.labels.find((l) =>
            l.name.toLowerCase().includes("bounty"),
        );
        const labelColor = bountyLabel ? `#${bountyLabel.color}` : "#ffd700";

        // Use unicode number emoji for first 10 issues as icons
        const icon = issueIcon(element.number);
        item.iconPath = new vscode.ThemeIcon(
            icon,
            new vscode.ThemeColor(`issues.${element.state === "open" ? "open" : "closed"}Icon`),
        );

        // Add context command so clicking opens the issue in browser.
        item.command = {
            command: "vscode.open",
            arguments: [vscode.Uri.parse(element.html_url)],
            title: "Open Bounty in Browser",
        };

        return item;
    }

    getChildren(): TreeIssue[] {
        return this.issues;
    }

    getParent(): undefined {
        return undefined;
    }
}

// Map issue number to a meaningful icon name supported by VS Code.
function issueIcon(n: number): string {
    const icons = [
        "circle-outline",       // 1
        "circle-filled",        // 2
        "symbol-number",        // 3
        "debug-breakpoint",     // 4
        "debug-breakpoint-unverified", // 5
        "debug-endpoint",       // 6
        " passes",      // 7
        "info",                 // 8
        "lightbulb",            // 9
        "star",                 // 10
    ];
    return icons[(n - 1) % icons.length];
}

// ---------------------------------------------------------------------------
// Quick-pick item for claiming
// ---------------------------------------------------------------------------

interface BountyQuickItem extends vscode.QuickPickItem {
    issue: GithubIssue;
}

// ---------------------------------------------------------------------------
// Main provider class
// ---------------------------------------------------------------------------

export class BountyBrowser implements vscode.Disposable {
    private provider: BountyTreeDataProvider;
    private view: vscode.TreeView<TreeIssue | null>;

    constructor(context: vscode.ExtensionContext) {
        this.provider = new BountyTreeDataProvider();

        this.view = vscode.window.createTreeView("rustchain.bountyBrowser", {
            treeDataProvider: this.provider,
            showCollapseAll: false,
        });
        context.subscriptions.push(this.view);

        // Refresh command
        context.subscriptions.push(
            vscode.commands.registerCommand(
                "rustchain.refreshBounties",
                () => this.provider.refresh(),
            ),
        );

        // Claim bounty — show quick-pick then open PR template
        context.subscriptions.push(
            vscode.commands.registerCommand(
                "rustchain.claimBounty",
                async () => {
                    await this.provider.refresh();
                    const issues = this.provider.issues;
                    if (issues.length === 0) {
                        void vscode.window.showInformationMessage(
                            "No open bounties found.",
                        );
                        return;
                    }

                    const picks: BountyQuickItem[] = issues.map((issue) => ({
                        label: `(#${issue.number}) ${issue.title}`,
                        description: issue.html_url,
                        detail: `Created: ${new Date(issue.created_at).toLocaleDateString()}`,
                        issue,
                    }));

                    const selected = await vscode.window.showQuickPick(picks, {
                        placeHolder: "Select a bounty to claim",
                    });

                    if (!selected) return;

                    const issue = selected.issue;
                    // Build PR creation URL with pre-filled template.
                    const prUrl = new URL(
                        `https://github.com/${REPO_OWNER}/${REPO_NAME}/compare/main...${REPO_OWNER}:bounty-${issue.number}?expand=1`,
                    );
                    prUrl.searchParams.set("title", `[Bounty #${issue.number}] ${issue.title}`);
                    prUrl.searchParams.set("body", `## Claiming Bounty #${issue.number}\n\n**Issue:** ${issue.title}\n**Link:** ${issue.html_url}\n\n### Work Summary\n<!-- Describe what you did -->\n\n### Checklist\n- [ ] Code follows project style\n- [ ] Tests added/updated\n- [ ] Documentation updated\n- [ ] PR targets \`main\` branch\n`);

                    void vscode.env.openExternal(vscode.Uri.parse(prUrl.toString()));

                    void vscode.window.showInformationMessage(
                        `Opening PR template for bounty #${issue.number}…`,
                    );
                },
            ),
        );

        // Initial load
        void this.provider.refresh();
    }

    dispose(): void {
        this.view.dispose();
    }
}
