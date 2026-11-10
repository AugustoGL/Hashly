import type { Metadata, Viewport } from "next";
import { Albert_Sans, Imbue } from "next/font/google";
import "./globals.css";

// Imbue: serif alta y condensada para la frase grande, en mayúsculas.
const imbue = Imbue({
  variable: "--font-imbue",
  subsets: ["latin"],
  axes: ["opsz"],
  display: "swap",
});

// Albert Sans: el texto.
const albert = Albert_Sans({
  variable: "--font-albert",
  subsets: ["latin"],
  display: "swap",
});

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Hashly: probá que tu archivo existía, sin mostrarlo",
  description:
    "Hashly reduce tus archivos a una huella de 32 bytes y la sella en Bitcoin. Cualquiera puede verificar la fecha; nadie puede ver el archivo.",
  applicationName: "Hashly",
  openGraph: {
    type: "website",
    locale: "es_AR",
    siteName: "Hashly",
    title: "Hashly: probá que tu archivo existía, sin mostrarlo",
    description: "Una huella de 32 bytes, sellada en Bitcoin. Los archivos nunca se guardan.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Hashly",
    description: "Prueba de existencia de archivos, sellada en Bitcoin.",
  },
};

export const viewport: Viewport = {
  themeColor: "#070b16",
  colorScheme: "dark",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className={`${imbue.variable} ${albert.variable} antialiased`} suppressHydrationWarning>
      <head>
        {/* Marca el documento para que las entradas animadas solo oculten contenido si hay JS. */}
        <script dangerouslySetInnerHTML={{ __html: "document.documentElement.classList.add('js')" }} />
      </head>
      <body>
        <a
          href="#contenido"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:bg-accent focus:px-4 focus:py-2 focus:text-accent-ink"
        >
          Saltar al contenido
        </a>
        {children}
      </body>
    </html>
  );
}
