export function Footer() {
  return (
    <footer className="py-6 md:px-8 md:py-0">
      <div className="flex flex-col items-center justify-between gap-4 md:h-16 md:flex-row">
        <p className="text-sm text-muted-foreground text-center md:text-left">
          Built with AgentWeave. © {new Date().getFullYear()} All rights
          reserved.
        </p>
        <p className="text-sm text-muted-foreground">
          <a
            href="#"
            className="underline underline-offset-4 hover:text-primary"
          >
            About
          </a>
        </p>
      </div>
    </footer>
  );
}
