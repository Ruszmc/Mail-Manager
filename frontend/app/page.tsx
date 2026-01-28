"use client";

import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Account = {
  id: number;
  email: string;
  imap_host: string;
  imap_port: number;
  imap_tls: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_tls: boolean;
};

type Thread = {
  id: number;
  subject: string | null;
  last_message_at: string | null;
  category: string;
  priority_score: number;
  priority_reason: string;
  is_newsletter: boolean;
};

type Message = {
  id: number;
  imap_uid: number;
  from_addr: string | null;
  subject: string | null;
  date: string | null;
  snippet: string | null;
  list_unsubscribe: string | null;
};

type Subscription = {
  id: number;
  sender: string;
  list_unsubscribe: string | null;
};

type UnsubscribeOptions = {
  mailto: string[];
  urls: string[];
};

export default function Home() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThread, setSelectedThread] = useState<Thread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState<string>("");
  const [summary, setSummary] = useState<string>("");
  const [actions, setActions] = useState<string[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string>("focus");
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [selectedSubscription, setSelectedSubscription] = useState<Subscription | null>(null);
  const [unsubscribeOptions, setUnsubscribeOptions] = useState<UnsubscribeOptions | null>(null);

  const threadIndex = useMemo(() => threads.findIndex((t) => t.id === selectedThread?.id), [threads, selectedThread]);

  useEffect(() => {
    fetch(`${API_URL}/accounts`)
      .then((res) => res.json())
      .then((data) => setAccounts(data))
      .catch(() => setToast("Accounts konnten nicht geladen werden."));
  }, []);

  useEffect(() => {
    if (!selectedAccount) return;
    fetch(`${API_URL}/threads/account/${selectedAccount.id}`)
      .then((res) => res.json())
      .then((data) => setThreads(data))
      .catch(() => setToast("Threads konnten nicht geladen werden."));

    fetch(`${API_URL}/threads/newsletters/${selectedAccount.id}`)
      .then((res) => res.json())
      .then((data) => setSubscriptions(data))
      .catch(() => setToast("Newsletter konnten nicht geladen werden."));
  }, [selectedAccount]);

  const filteredThreads = threads.filter((thread) => {
    if (activeTab === "newsletters") return thread.is_newsletter;
    if (activeTab === "needs-reply") return thread.priority_score > 60;
    if (activeTab === "all") return true;
    return thread.priority_score >= 40 && !thread.is_newsletter;
  });

  useEffect(() => {
    if (!selectedThread) return;
    fetch(`${API_URL}/threads/${selectedThread.id}/messages`)
      .then((res) => res.json())
      .then((data) => setMessages(data))
      .catch(() => setToast("Nachrichten konnten nicht geladen werden."));

    fetch(`${API_URL}/threads/${selectedThread.id}/insights`)
      .then((res) => res.json())
      .then((data) => {
        setSummary(data.summary);
        setActions(data.actions);
        setLabels(data.labels);
      })
      .catch(() => setToast("Insights konnten nicht geladen werden."));
  }, [selectedThread]);

  useEffect(() => {
    if (!selectedSubscription) return;
    fetch(`${API_URL}/threads/newsletters/${selectedSubscription.id}/unsubscribe`)
      .then((res) => res.json())
      .then((data) => setUnsubscribeOptions(data))
      .catch(() => setToast("Unsubscribe Optionen konnten nicht geladen werden."));
  }, [selectedSubscription]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "?") setShowShortcuts(true);
      if (event.key === "j") {
        const next = filteredThreads[threadIndex + 1] || filteredThreads[0];
        if (next) setSelectedThread(next);
      }
      if (event.key === "k") {
        const prev = filteredThreads[threadIndex - 1] || filteredThreads[filteredThreads.length - 1];
        if (prev) setSelectedThread(prev);
      }
      if (event.key === "s" && selectedThread) {
        requestSummary(selectedThread.id);
      }
      if (event.key === "r" && selectedThread) {
        requestDraft(selectedThread.id);
      }
      if (event.key === "Escape") setShowShortcuts(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [filteredThreads, threadIndex, selectedThread]);

  const requestSummary = (threadId: number) => {
    fetch(`${API_URL}/threads/${threadId}/ai/summarize`, { method: "POST" })
      .then((res) => res.json())
      .then((data) => setSummary(data.result))
      .catch(() => setToast("Zusammenfassung fehlgeschlagen."));
  };

  const requestDraft = (threadId: number) => {
    fetch(`${API_URL}/threads/${threadId}/ai/draft`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language: "de" }),
    })
      .then((res) => res.json())
      .then((data) => setDraft(data.result))
      .catch(() => setToast("Entwurf fehlgeschlagen."));
  };

  const syncNow = () => {
    if (!selectedAccount) return;
    fetch(`${API_URL}/accounts/${selectedAccount.id}/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limit: 50 }),
    })
      .then((res) => res.json())
      .then(() => {
        setToast("Sync abgeschlossen");
        return fetch(`${API_URL}/threads/account/${selectedAccount.id}`);
      })
      .then((res) => res.json())
      .then((data) => setThreads(data))
      .catch(() => setToast("Sync fehlgeschlagen."));
  };

  const addAccount = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    const res = await fetch(`${API_URL}/accounts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
        imap_host: payload.imap_host,
        imap_port: Number(payload.imap_port),
        imap_tls: payload.imap_tls === "on",
        smtp_host: payload.smtp_host,
        smtp_port: Number(payload.smtp_port),
        smtp_tls: payload.smtp_tls === "on",
      }),
    });
    if (!res.ok) {
      setToast("Account konnte nicht gespeichert werden.");
      return;
    }
    const data = await res.json();
    setAccounts((prev) => [data, ...prev]);
    setSelectedAccount(data);
    event.currentTarget.reset();
  };

  const testConnection = async (event: React.MouseEvent<HTMLButtonElement>) => {
    event.preventDefault();
    const form = event.currentTarget.form;
    if (!form) return;
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    const res = await fetch(`${API_URL}/accounts/test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: payload.email,
        password: payload.password,
        imap_host: payload.imap_host,
        imap_port: Number(payload.imap_port),
        imap_tls: payload.imap_tls === "on",
      }),
    });
    if (res.ok) {
      setToast("IMAP Verbindung erfolgreich.");
    } else {
      setToast("IMAP Verbindung fehlgeschlagen.");
    }
  };

  return (
    <div className="min-h-screen bg-ink text-white">
      <header className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
        <div>
          <h1 className="text-xl font-semibold">MailPilot</h1>
          <p className="text-sm text-slate-400">AI-assisted email client</p>
        </div>
        <div className="flex items-center gap-3">
          <button className="rounded-full bg-accent px-4 py-2 text-sm font-semibold" onClick={syncNow}>
            Sync Now
          </button>
          <button className="text-sm text-slate-300" onClick={() => setShowShortcuts(true)}>
            Shortcuts ?
          </button>
        </div>
      </header>

      <main className="grid grid-cols-[280px_1fr_360px] gap-4 px-6 py-6">
        <aside className="space-y-6">
          <section className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-300">Accounts</h2>
            <div className="mt-3 space-y-2">
              {accounts.map((account) => (
                <button
                  key={account.id}
                  className={clsx(
                    "w-full rounded-xl px-3 py-2 text-left text-sm",
                    selectedAccount?.id === account.id ? "bg-accent/20" : "bg-slate-800/60"
                  )}
                  onClick={() => setSelectedAccount(account)}
                >
                  <div className="font-medium">{account.email}</div>
                  <div className="text-xs text-slate-400">{account.imap_host}</div>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-300">Add account</h2>
            <form className="mt-3 space-y-3 text-sm" onSubmit={addAccount}>
              <input name="email" placeholder="Email" className="w-full rounded-lg bg-slate-800 px-3 py-2" required />
              <input name="password" type="password" placeholder="App password" className="w-full rounded-lg bg-slate-800 px-3 py-2" required />
              <input name="imap_host" placeholder="IMAP host" className="w-full rounded-lg bg-slate-800 px-3 py-2" required />
              <input name="imap_port" placeholder="IMAP port" className="w-full rounded-lg bg-slate-800 px-3 py-2" defaultValue={993} required />
              <label className="flex items-center gap-2 text-xs text-slate-300">
                <input name="imap_tls" type="checkbox" defaultChecked /> IMAP TLS
              </label>
              <input name="smtp_host" placeholder="SMTP host" className="w-full rounded-lg bg-slate-800 px-3 py-2" required />
              <input name="smtp_port" placeholder="SMTP port" className="w-full rounded-lg bg-slate-800 px-3 py-2" defaultValue={587} required />
              <label className="flex items-center gap-2 text-xs text-slate-300">
                <input name="smtp_tls" type="checkbox" defaultChecked /> SMTP TLS
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button className="rounded-lg bg-slate-700 px-3 py-2 text-xs" onClick={testConnection}>
                  Test connection
                </button>
                <button className="rounded-lg bg-accent px-3 py-2 text-xs font-semibold" type="submit">
                  Save account
                </button>
              </div>
            </form>
          </section>
        </aside>

        <section className="space-y-4">
          <div className="flex gap-2">
            {[
              { key: "focus", label: "Focus Inbox" },
              { key: "newsletters", label: "Newsletters" },
              { key: "needs-reply", label: "Needs Reply" },
              { key: "all", label: "All" },
            ].map((tab) => (
              <button
                key={tab.key}
                className={clsx(
                  "rounded-full px-3 py-1 text-xs",
                  activeTab === tab.key ? "bg-accent" : "bg-slate-800"
                )}
                onClick={() => setActiveTab(tab.key)}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <div className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-300">Threads</h2>
            <div className="mt-3 space-y-2">
              {activeTab !== "newsletters" &&
                filteredThreads.map((thread) => (
                  <button
                    key={thread.id}
                  className={clsx(
                    "flex w-full items-start justify-between rounded-xl px-3 py-2 text-left",
                    selectedThread?.id === thread.id ? "bg-accent/20" : "bg-slate-800/60"
                  )}
                  onClick={() => setSelectedThread(thread)}
                >
                  <div>
                    <div className="text-sm font-medium">{thread.subject || "(Ohne Betreff)"}</div>
                    <div className="text-xs text-slate-400">{thread.priority_reason}</div>
                  </div>
                  <span className="badge bg-slate-700 text-white">{thread.priority_score}</span>
                  </button>
                ))}
              {activeTab === "newsletters" && (
                <div className="space-y-2">
                  {subscriptions.map((subscription) => (
                    <button
                      key={subscription.id}
                      className={clsx(
                        "w-full rounded-xl px-3 py-2 text-left text-sm",
                        selectedSubscription?.id === subscription.id ? "bg-accent/20" : "bg-slate-800/60"
                      )}
                      onClick={() => setSelectedSubscription(subscription)}
                    >
                      <div className="font-medium">{subscription.sender}</div>
                      <div className="text-xs text-slate-400">Newsletter</div>
                    </button>
                  ))}
                </div>
              )}
              {!filteredThreads.length && activeTab !== "newsletters" && (
                <p className="text-xs text-slate-500">Keine Threads.</p>
              )}
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-300">Thread Details</h2>
            {selectedThread ? (
              <>
                <div className="mt-3 space-y-2">
                  <h3 className="text-lg font-semibold">{selectedThread.subject || "(Ohne Betreff)"}</h3>
                  <div className="flex flex-wrap gap-2">
                    {labels.map((label) => (
                      <span key={label} className="badge bg-slate-700 text-white">{label}</span>
                    ))}
                  </div>
                  <p className="text-sm text-slate-300">{summary}</p>
                  <ul className="list-disc pl-5 text-sm text-slate-300">
                    {actions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                  <div className="flex gap-2">
                    <button className="rounded-lg bg-accent px-3 py-2 text-xs" onClick={() => requestSummary(selectedThread.id)}>
                      Summarize
                    </button>
                    <button className="rounded-lg bg-slate-700 px-3 py-2 text-xs" onClick={() => requestDraft(selectedThread.id)}>
                      Draft Reply
                    </button>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  {messages.map((message) => (
                    <div key={message.id} className="rounded-xl bg-slate-800/70 p-3">
                      <div className="text-xs text-slate-400">{message.from_addr}</div>
                      <div className="text-sm">{message.snippet}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <p className="mt-3 text-sm text-slate-400">Wähle einen Thread aus.</p>
            )}
          </div>

          {activeTab === "newsletters" && (
            <div className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
              <h2 className="text-sm font-semibold text-slate-300">Unsubscribe</h2>
              {selectedSubscription ? (
                <div className="mt-3 space-y-2 text-sm text-slate-300">
                  <p>{selectedSubscription.sender}</p>
                  {unsubscribeOptions?.mailto?.length ? (
                    <div>
                      <p className="text-xs text-slate-400">Mailto</p>
                      {unsubscribeOptions.mailto.map((link) => (
                        <button
                          key={link}
                          className="mt-1 w-full rounded-lg bg-slate-800 px-3 py-2 text-left text-xs"
                          onClick={() => navigator.clipboard.writeText(link)}
                        >
                          Copy {link}
                        </button>
                      ))}
                    </div>
                  ) : null}
                  {unsubscribeOptions?.urls?.length ? (
                    <div>
                      <p className="text-xs text-slate-400">URL</p>
                      {unsubscribeOptions.urls.map((link) => (
                        <a
                          key={link}
                          className="mt-1 block rounded-lg bg-slate-800 px-3 py-2 text-xs text-accent"
                          href={link}
                          target="_blank"
                          rel="noreferrer"
                        >
                          Open unsubscribe link
                        </a>
                      ))}
                    </div>
                  ) : null}
                  {!unsubscribeOptions?.mailto?.length && !unsubscribeOptions?.urls?.length && (
                    <p className="text-xs text-slate-400">Keine Unsubscribe-Links gefunden.</p>
                  )}
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-400">Wähle ein Newsletter-Abo aus.</p>
              )}
            </div>
          )}

          <div className="rounded-2xl bg-slate-900/60 p-4 shadow-lg">
            <h2 className="text-sm font-semibold text-slate-300">Reply Draft</h2>
            <textarea
              className="mt-3 w-full rounded-xl bg-slate-800 p-3 text-sm"
              rows={6}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Draft reply..."
            />
            <p className="text-xs text-slate-500">Replies are never auto-sent. Copy/paste or send manually.</p>
          </div>
        </section>
      </main>

      {toast && (
        <div className="fixed bottom-6 right-6 rounded-xl bg-slate-900 px-4 py-2 text-sm shadow-lg" onClick={() => setToast(null)}>
          {toast}
        </div>
      )}

      {showShortcuts && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/70">
          <div className="rounded-2xl bg-slate-900 p-6 text-sm text-slate-200 shadow-xl">
            <h3 className="text-lg font-semibold">Shortcuts</h3>
            <ul className="mt-3 space-y-1">
              <li>j / k: Move in thread list</li>
              <li>r: Draft reply</li>
              <li>s: Summarize</li>
              <li>?: Open this modal</li>
              <li>Esc: Close</li>
            </ul>
            <button className="mt-4 w-full rounded-lg bg-accent px-3 py-2" onClick={() => setShowShortcuts(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
