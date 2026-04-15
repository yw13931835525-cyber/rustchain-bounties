// SPDX-License-Identifier: MIT
/**
 * Status-bar item that shows whether the configured miner is actively
 * attesting on the RustChain network.
 *
 * Green  "$(debug-stop) RTC: attesting"  → miner is attesting
 * Red    "$(error) RTC: not attesting"    → miner exists but not attesting
 * Grey   "$(question) RTC: offline"      → node unreachable
 */

import * as vscode from "vscode";
import { fetchMinerStatus } from "./rustchainApi";

const DEFAULT_REFRESH_SECONDS = 60;
const MIN_REFRESH_SECONDS = 15;

export class MinerStatusBar implements vscode.Disposable {
    private readonly item: vscode.StatusBarItem;
    private timer: ReturnType<typeof setInterval> | undefined;

    constructor(context: vscode.ExtensionContext) {
        this.item = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            51,
        );
        this.item.command = "rustchain.checkNodeHealth";
        this.item.tooltip = "Click to check RustChain node health";
        context.subscriptions.push(this.item);

        this.startPolling();
        this.refresh();
    }

    async refresh(): Promise<void> {
        const config = vscode.workspace.getConfiguration("rustchain");
        const minerId = config.get<string>("minerId", "");

        if (!minerId) {
            this.item.text = "$(question) RTC: set wallet";
            this.item.color = undefined;
            this.item.show();
            return;
        }

        try {
            const isAttesting = await fetchMinerStatus(minerId);
            if (isAttesting === null) {
                this.item.text = "$(debug-stop) RTC: unknown";
                this.item.color = "yellow";
            } else if (isAttesting) {
                this.item.text = "$(debug-stop) RTC: attesting";
                this.item.color = "#4caf50"; // green
            } else {
                this.item.text = "$(error) RTC: not attesting";
                this.item.color = "#f44336"; // red
            }
        } catch {
            this.item.text = "$(question) RTC: offline";
            this.item.color = "#9e9e9e"; // grey
        }

        this.item.show();
    }

    onConfigChange(): void {
        this.stopPolling();
        this.startPolling();
        this.refresh();
    }

    dispose(): void {
        this.stopPolling();
        this.item.dispose();
    }

    private startPolling(): void {
        const config = vscode.workspace.getConfiguration("rustchain");
        let intervalSec = config.get<number>(
            "minerRefreshInterval",
            DEFAULT_REFRESH_SECONDS,
        );
        if (intervalSec < MIN_REFRESH_SECONDS) {
            intervalSec = MIN_REFRESH_SECONDS;
        }

        this.timer = setInterval(() => {
            this.refresh();
        }, intervalSec * 1000);
    }

    private stopPolling(): void {
        if (this.timer !== undefined) {
            clearInterval(this.timer);
            this.timer = undefined;
        }
    }
}
