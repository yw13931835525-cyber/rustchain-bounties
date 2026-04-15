// SPDX-License-Identifier: MIT
/**
 * Status-bar item that counts down to the next RustChain epoch.
 *
 * Displays: "$(clock) Epoch 42 — 3m 24s"
 *
 * Epoch duration is derived from `blocks_per_epoch` (each slot ≈ 1 second).
 */

import * as vscode from "vscode";
import { fetchEpoch } from "./rustchainApi";

export class EpochTimer implements vscode.Disposable {
    private readonly item: vscode.StatusBarItem;
    private timer: ReturnType<typeof setInterval> | undefined;
    private cachedBlocksPerEpoch: number = 100; // sensible default

    constructor(context: vscode.ExtensionContext) {
        this.item = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            50,
        );
        this.item.command = "rustchain.checkNodeHealth";
        this.item.tooltip = "RustChain epoch countdown — click for node info";
        context.subscriptions.push(this.item);

        // Tick every second for smooth countdown.
        this.timer = setInterval(() => this.tick(), 1_000);
        context.subscriptions.push(this);

        // Fetch epoch info to get blocks_per_epoch.
        this.refresh();
    }

    private async refresh(): Promise<void> {
        try {
            const epoch = await fetchEpoch();
            this.cachedBlocksPerEpoch = epoch.blocks_per_epoch || 100;
            this.updateDisplay(epoch.slot, epoch.epoch);
        } catch {
            this.item.text = "$(clock) RTC: offline";
            this.item.color = "#9e9e9e";
            this.item.show();
        }
    }

    private tick(): void {
        // We need current slot — ask the API each tick (epoch advances ~1/sec).
        fetchEpoch()
            .then((epoch) => {
                this.cachedBlocksPerEpoch = epoch.blocks_per_epoch || 100;
                this.updateDisplay(epoch.slot, epoch.epoch);
            })
            .catch(() => {
                this.item.text = "$(clock) RTC: offline";
                this.item.color = "#9e9e9e";
            });
    }

    private updateDisplay(currentSlot: number, epoch: number): void {
        const bpe = this.cachedBlocksPerEpoch;
        const slotInEpoch = currentSlot % bpe;
        const remainingSlots = bpe - slotInEpoch;
        const remainingSec = remainingSlots;

        if (remainingSec < 0) {
            this.item.text = `$(clock) Epoch ${epoch} — --`;
            return;
        }

        const mm = String(Math.floor(remainingSec / 60)).padStart(2, "0");
        const ss = String(remainingSec % 60).padStart(2, "0");
        this.item.text = `$(clock) Epoch ${epoch} — ${mm}m ${ss}s`;
        this.item.color = remainingSec < 60 ? "#ff9800" : undefined; // orange when < 1 min
        this.item.show();
    }

    dispose(): void {
        if (this.timer !== undefined) {
            clearInterval(this.timer);
            this.timer = undefined;
        }
        this.item.dispose();
    }
}
