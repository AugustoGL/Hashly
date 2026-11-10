import { Nav } from "@/components/Nav";
import { Reveal } from "@/components/Reveal";
import { SmoothScroll } from "@/components/SmoothScroll";
import { Story } from "@/components/story/Story";
import { Showcase } from "@/components/sections/Showcase";
import { Pricing } from "@/components/sections/Pricing";
import { Remains } from "@/components/sections/Remains";
import { Cta, Faq, Footer } from "@/components/sections/Closing";

export default function Home() {
  return (
    <>
      <SmoothScroll />
      <Reveal />
      <Nav />
      <main id="contenido">
        <Story />
        <Showcase />
        <Pricing />
        <Remains />
        <Faq />
        <Cta />
      </main>
      <Footer />
    </>
  );
}
