// SPDX-License-Identifier: MIT
/**
 * RustChain Development Tools — VS Code Extension
 *
 * Provides:
 * - RTC balance display in the status bar
 * - Miner attesting status indicator (green/red)
 * - Epoch countdown timer in the status bar
 * - Bounty browser sidebar (open RustChain bounties)
 * - RustChain config file syntax highlighting
 * - Code snippets for RustChain development
 *
 * Bounty: #2868
 */

import * as vscode from "vscode";
import { BalanceStatusBar } from "./balanceStatusBar";
import { MinerStatusBar } from "./minerStatus";
import { EpochTimer } from "./epochTimer";
import { NodeHealthChecker } from "./nodeHealth";
import { BountyBrowser } from "./bountyBrowser";

let balanceStatusBar: BalanceStatusBar | undefined;
let minerStatusBar: MinerStatusBar | undefined;
let epochTimer: EpochTimer | undefined;
let nodeHealthChecker: NodeHealthChecker | undefined;
let bountyBrowser: BountyBrowser | undefined;

export function activate(context: vscode.ExtensionContext): void {
    // --- Status bar: RTC balance ---
    balanceStatusBar = new BalanceStatusBar(context);

    // --- Status bar: miner attesting status ---
    minerStatusBar = new MinerStatusBar(context);

    // --- Status bar: epoch countdown ---
    epochTimer = new EpochTimer(context);

    // --- Node health checker ---
    nodeHealthChecker = new NodeHealthChecker();

    // --- Bounty browser sidebar ---
    bountyBrowser = new BountyBrowser(context);

    // --- Commands ---
    context.subscriptions.push(
        vscode.commands.registerCommand("rustchain.refreshBalance", () => {
            balanceStatusBar?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("rustchain.refreshMinerStatus", () => {
            minerStatusBar?.refresh();
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("rustchain.setMinerId", async () => {
            const config = vscode.workspace.getConfiguration("rustchain");
            const current = config.get<string>("minerId", "");
            const minerId = await vscode.window.showInputBox({
                prompt: "Enter your RustChain miner/wallet ID",
                placeHolder: "e.g. hebeigaoruan-rtc",
                value: current,
            });
            if (minerId !== undefined) {
                await vscode.workspace
                    .getConfiguration("rustchain")
                    .update("minerId", minerId, vscode.ConfigurationTarget.Global);
                balanceStatusBar?.refresh();
                minerStatusBar?.refresh();
            }
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand("rustchain.checkNodeHealth", async () => {
            await nodeHealthChecker?.showHealth();
        }),
    );

    // React to configuration changes.
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration("rustchain")) {
                balanceStatusBar?.onConfigChange();
                minerStatusBar?.onConfigChange();
            }
        }),
    );
}

export function deactivate(): void {
    balanceStatusBar?.dispose();
    balanceStatusBar = undefined;
    minerStatusBar?.dispose();
    minerStatusBar = undefined;
    epochTimer?.dispose();
    epochTimer = undefined;
    nodeHealthChecker = undefined;
    bountyBrowser?.dispose();
    bountyBrowser = undefined;
}
