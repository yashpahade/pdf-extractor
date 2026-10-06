import { type ReactNode } from "react";

interface Props {
  sidebar: ReactNode;
  main: ReactNode;
  chat: ReactNode;
}

export default function Layout({ sidebar, main, chat }: Props) {
  return (
    <div className="layout">
      <aside className="layout__sidebar">
        <div className="layout__sidebar-header">
          <h1 className="layout__logo">📄 DocSummarizer</h1>
        </div>
        {sidebar}
      </aside>
      <main className="layout__main">{main}</main>
      <aside className="layout__chat">{chat}</aside>
    </div>
  );
}
