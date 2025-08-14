declare module 'remark-gfm' {
  const plugin: any;
  export default plugin;
}

declare module 'remark-math' {
  const plugin: any;
  export default plugin;
}

declare module 'rehype-katex' {
  const plugin: any;
  export default plugin;
}

declare module 'rehype-raw' {
  const plugin: any;
  export default plugin;
}

declare module 'katex' {
  export function renderToString(tex: string, options?: any): string;
}
