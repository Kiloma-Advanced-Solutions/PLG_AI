import type { Pluggable } from 'unified';

declare module 'remark-gfm' {
  const plugin: Pluggable;
  export default plugin;
}

declare module 'remark-math' {
  const plugin: Pluggable;
  export default plugin;
}

declare module 'rehype-katex' {
  const plugin: Pluggable;
  export default plugin;
}

declare module 'rehype-raw' {
  const plugin: Pluggable;
  export default plugin;
}

declare module 'katex' {
  export function renderToString(tex: string, options?: Record<string, unknown>): string;
}
