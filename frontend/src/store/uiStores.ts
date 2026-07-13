/**
 * Preview store — holds HTML content for immediate iframe preview
 * after a successful generation, before the API round-trip completes.
 */

import { create } from 'zustand';

export interface PreviewState {
  htmlContent: string | null;
  setHtmlContent: (html: string | null) => void;
  clear: () => void;
}
export const usePreviewStore = create<PreviewState>((set) => ({
  htmlContent: null,
  setHtmlContent: (html) => set({ htmlContent: html }),
  clear: () => set({ htmlContent: null }),
}));
