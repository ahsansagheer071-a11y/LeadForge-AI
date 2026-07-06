/**
 * Preview store + Deployment store + Notifications store.
 * Kept small & complementary to UI shells.
 */

import { create } from 'zustand';
import type { PreviewInfo, DeploymentInfo } from '@/types';

/* ─── Preview ──────────────────────────────────────────────── */
export interface PreviewState {
  info: PreviewInfo | null;
  htmlContent: string | null;
  setInfo: (i: PreviewInfo | null) => void;
  setHtmlContent: (html: string | null) => void;
  clear: () => void;
}
export const usePreviewStore = create<PreviewState>((set) => ({
  info: null,
  htmlContent: null,
  setInfo: (i) => set({ info: i }),
  setHtmlContent: (html) => set({ htmlContent: html }),
  clear: () => set({ info: null, htmlContent: null }),
}));

/* ─── Deployment ──────────────────────────────────────────── */
export interface DeploymentState {
  deployments: DeploymentInfo[];
  setDeployments: (d: DeploymentInfo[]) => void;
  append: (d: DeploymentInfo) => void;
  update: (id: string, patch: Partial<DeploymentInfo>) => void;
  clear: () => void;
}
export const useDeploymentStore = create<DeploymentState>((set) => ({
  deployments: [],
  setDeployments: (d) => set({ deployments: d }),
  append: (d) => set((s) => ({ deployments: [d, ...s.deployments] })),
  update: (id, patch) =>
    set((s) => ({
      deployments: s.deployments.map((d) => (d.id === id ? { ...d, ...patch } : d)),
    })),
  clear: () => set({ deployments: [] }),
}));

/* ─── Notifications ──────────────────────────────────────── */
import type { AppNotification } from '@/types';

export interface NotificationsState {
  items: AppNotification[];
  setItems: (items: AppNotification[]) => void;
  push: (n: AppNotification) => void;
  markRead: (id: string) => void;
  markAllRead: () => void;
  unreadCount: () => number;
}
export const useNotificationsStore = create<NotificationsState>((set, get) => ({
  items: [],
  setItems: (items) => set({ items }),
  push: (n) => set((s) => ({ items: [n, ...s.items] })),
  markRead: (id) =>
    set((s) => ({
      items: s.items.map((x) => (x.id === id ? { ...x, read: true } : x)),
    })),
  markAllRead: () => set((s) => ({ items: s.items.map((x) => ({ ...x, read: true })) })),
  unreadCount: () => get().items.filter((x) => !x.read).length,
}));