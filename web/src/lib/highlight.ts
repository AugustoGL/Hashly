import "server-only";
import { createCssVariablesTheme, getSingletonHighlighter } from "shiki";

// Los colores salen de variables CSS (--shiki-*), así el código cambia con el tema
// sin volver a resaltar. Todo se resuelve en el servidor: 0 KB de Shiki en el cliente.
const theme = createCssVariablesTheme({ name: "hashly", variablePrefix: "--shiki-", fontStyle: true });

export type Lang = "bash" | "javascript" | "json" | "python";

export async function highlight(code: string, lang: Lang): Promise<string> {
  "use cache";
  const highlighter = await getSingletonHighlighter({ themes: [theme], langs: ["bash", "javascript", "json", "python"] });
  return highlighter.codeToHtml(code.trim(), { lang, theme: "hashly" });
}
