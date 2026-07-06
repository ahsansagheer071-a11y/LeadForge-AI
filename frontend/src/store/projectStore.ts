/**
 * Project store — currently-selected project + cached list.
 */

import { create } from 'zustand';
import type { Project } from '@/types';

export interface ProjectState {
  current: Project | null;
  list: Project[];

  setCurrent: (p: Project | null) => void;
  setList: (list: Project[]) => void;
  upsert: (p: Project) => void;
  remove: (id: string) => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  current: null,
  list: [],

  setCurrent: (p) => set({ current: p }),
  setList: (list) => set({ list }),
  upsert: (p) =>
    set((s) => {
      const idx = s.list.findIndex((x) => x.id === p.id);
      if (idx >= 0) {
        const copy = [...s.list];
        copy[idx] = p;
        return { list: copy };
      }
      return { list: [p, ...s.list] };
    }),
  remove: (id) =>
    set((s) => ({
      list: s.list.filter((p) => p.id !== id),
      current: s.current?.id === id ? null : s.current,
    })),
}));
