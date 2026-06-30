import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { AnimatePresence, motion } from "framer-motion";
import "./index.css";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const TEMP_SIGNALS_KEY = "jotpop_temp_onboarding_signals";
const ONBOARDING_DONE_KEY = "jotpop_onboarding_demo_done";
const AUTH_TOKEN_KEY = "jotpop_auth_token";
const SIGNALS_IMPORTED_PREFIX = "jotpop_signals_imported_user_";
const STEP26_QA_KEY = "jotpop_step26_manual_qa";

const STEP26_QA_ITEMS = [
  { id: "auth", title: "Sign in", hint: "ale@example.com logs in and lands on Feed." },
  { id: "feed_stack", title: "Feed stack", hint: "Full-screen mobile card plus cards behind it are visible." },
  { id: "feed_gestures", title: "Feed gestures", hint: "Whole-card right/left chooses, up skips, down goes previous." },
  { id: "micro_jot", title: "Micro-Jot", hint: "Empty right swipe shakes; empty upward swipe skips; written Jot saves." },
  { id: "forge_lock", title: "Forge lock", hint: "Suggestions appear before lock; exactly 3 are locked." },
  { id: "forge_ritual", title: "Forge ritual", hint: "Swipe triggers hammer, sparks, glow, no sounds." },
  { id: "evolution", title: "Evolution", hint: "Avatar, Pattern Map, Follow-through and compact achievements work." },
  { id: "jot_foundation", title: "Jot foundation", hint: "Jot Trail and Next Insight live in Evolution as compact expandable sections." },
  { id: "dev_tools", title: "Dev tools", hint: "Only dev user sees the Dev button and smoke check." },
  { id: "normal_clean", title: "Normal UI clean", hint: "No backend/debug wording in normal Feed, Forge or Evolution." },
];

const themeMap = {
  signal: {
    shell: "from-cyan-500/25 via-zinc-950 to-violet-500/20",
    glow: "shadow-cyan-500/20",
    border: "border-cyan-300/30",
    text: "text-cyan-100",
    chip: "bg-cyan-300 text-zinc-950",
  },
  void: {
    shell: "from-violet-500/25 via-zinc-950 to-fuchsia-500/20",
    glow: "shadow-violet-500/20",
    border: "border-violet-300/30",
    text: "text-violet-100",
    chip: "bg-violet-200 text-zinc-950",
  },
  gold: {
    shell: "from-amber-500/25 via-zinc-950 to-yellow-500/15",
    glow: "shadow-amber-500/20",
    border: "border-amber-300/30",
    text: "text-amber-100",
    chip: "bg-amber-200 text-zinc-950",
  },
  ember: {
    shell: "from-orange-600/25 via-zinc-950 to-red-500/20",
    glow: "shadow-orange-500/20",
    border: "border-orange-300/30",
    text: "text-orange-100",
    chip: "bg-orange-200 text-zinc-950",
  },
  deepblue: {
    shell: "from-blue-600/25 via-zinc-950 to-sky-500/15",
    glow: "shadow-blue-500/20",
    border: "border-blue-300/30",
    text: "text-blue-100",
    chip: "bg-blue-200 text-zinc-950",
  },
  pulse: {
    shell: "from-rose-500/25 via-zinc-950 to-pink-500/15",
    glow: "shadow-rose-500/20",
    border: "border-rose-300/30",
    text: "text-rose-100",
    chip: "bg-rose-200 text-zinc-950",
  },
  aether: {
    shell: "from-indigo-500/25 via-zinc-950 to-teal-500/15",
    glow: "shadow-indigo-500/20",
    border: "border-indigo-300/30",
    text: "text-indigo-100",
    chip: "bg-indigo-200 text-zinc-950",
  },
};

function getStoredSignals() {
  try {
    return JSON.parse(localStorage.getItem(TEMP_SIGNALS_KEY) || "[]");
  } catch {
    return [];
  }
}

function getStoredToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

function parseApiError(error, fallback) {
  return error?.response?.data?.detail || error?.response?.data?.message || fallback;
}

function getStoredQaState() {
  try {
    const raw = JSON.parse(localStorage.getItem(STEP26_QA_KEY) || "{}");
    return STEP26_QA_ITEMS.reduce((acc, item) => {
      acc[item.id] = Boolean(raw[item.id]);
      return acc;
    }, {});
  } catch {
    return STEP26_QA_ITEMS.reduce((acc, item) => {
      acc[item.id] = false;
      return acc;
    }, {});
  }
}

function shuffleCards(cards) {
  return [...(cards || [])]
    .map((card) => ({ card, sort: Math.random() }))
    .sort((a, b) => a.sort - b.sort)
    .map(({ card }) => card);
}

function rhythmType(card) {
  return card?.type || "card";
}

function wouldMakeTriple(deck, card) {
  if (deck.length < 2 || !card) return false;
  const nextType = rhythmType(card);
  return rhythmType(deck[deck.length - 1]) === nextType && rhythmType(deck[deck.length - 2]) === nextType;
}

function buildNoTripleDeck(cards) {
  const pool = [...cards];
  const deck = [];

  while (pool.length) {
    let index = pool.findIndex((candidate) => !wouldMakeTriple(deck, candidate));
    if (index < 0) index = 0;
    const [next] = pool.splice(index, 1);
    deck.push(next);
  }

  return deck;
}

function prepareFeedDeck(cards) {
  const shuffled = shuffleCards(cards || []);
  const microJots = shuffled.filter((card) => card?.type === "micro_jot");
  const regularCards = shuffled.filter((card) => card?.type !== "micro_jot");
  const regularDeck = buildNoTripleDeck(regularCards);
  const mixed = [];
  let microIndex = 0;
  let nextMicroSlot = 8 + Math.floor(Math.random() * 5);

  regularDeck.forEach((card) => {
    mixed.push(card);
    if (microIndex < microJots.length && mixed.length >= nextMicroSlot) {
      mixed.push(microJots[microIndex]);
      microIndex += 1;
      nextMicroSlot += 9 + Math.floor(Math.random() * 5);
    }
  });

  while (microIndex < microJots.length) {
    mixed.push(microJots[microIndex]);
    microIndex += 1;
  }

  return buildNoTripleDeck(mixed);
}


export default function App() {
  const [apiStatus, setApiStatus] = useState("checking");
  const [apiVersion, setApiVersion] = useState("");
  const [token, setToken] = useState(() => getStoredToken());
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState("feed");
  const [authMode, setAuthMode] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  const [onboardingCards, setOnboardingCards] = useState([]);
  const [feedCards, setFeedCards] = useState([]);
  const [loadingCards, setLoadingCards] = useState(true);
  const [cardsError, setCardsError] = useState("");
  const [tempSignals, setTempSignals] = useState(() => getStoredSignals());
  const [lastOnboardingChoice, setLastOnboardingChoice] = useState(null);

  const [feedIndex, setFeedIndex] = useState(0);
  const [feedStatus, setFeedStatus] = useState("idle");
  const [feedMessage, setFeedMessage] = useState("");

  const [jotSummary, setJotSummary] = useState(null);
  const [jotsLoading, setJotsLoading] = useState(false);
  const [jotsError, setJotsError] = useState("");

  const [promiseSuggestions, setPromiseSuggestions] = useState([]);
  const [todayPromises, setTodayPromises] = useState(null);
  const [selectedPromiseIds, setSelectedPromiseIds] = useState([]);
  const [promisesLoading, setPromisesLoading] = useState(false);
  const [promisesError, setPromisesError] = useState("");
  const [promiseMessage, setPromiseMessage] = useState("");
  const [forgingPromiseId, setForgingPromiseId] = useState(null);
  const [forgeToast, setForgeToast] = useState(null);

  const [insightStatus, setInsightStatus] = useState(null);
  const [insightMessage, setInsightMessage] = useState("");
  const [evolutionSummary, setEvolutionSummary] = useState(null);
  const [evolutionLoading, setEvolutionLoading] = useState(false);
  const [evolutionError, setEvolutionError] = useState("");

  const [devStatus, setDevStatus] = useState(null);
  const [devLoading, setDevLoading] = useState(false);
  const [devError, setDevError] = useState("");
  const [devSmoke, setDevSmoke] = useState(null);
  const [devSmokeLoading, setDevSmokeLoading] = useState(false);
  const [devSmokeError, setDevSmokeError] = useState("");

  const isLoggedIn = Boolean(token && currentUser);
  const isDev = Boolean(currentUser?.is_dev);
  const character = currentUser?.active_character || null;
  const onboardingComplete = tempSignals.length >= 7;
  const currentOnboardingCard = onboardingCards[tempSignals.length] || null;

  useEffect(() => {
    loadHealth();
    loadOnboardingCards();
    loadFeedCards();
  }, []);

  useEffect(() => {
    if (!token) {
      setCurrentUser(null);
      setInsightStatus(null);
      setEvolutionSummary(null);
      setJotSummary(null);
      setDevStatus(null);
      setDevError("");
      setDevSmoke(null);
      setDevSmokeError("");
      setTodayPromises(null);
      setPromiseSuggestions([]);
      return;
    }

    fetchCurrentUser(token);
    fetchPromiseData(token);
    fetchInsightStatus(token);
    fetchJotSummary(token);
    fetchEvolutionSummary(token);
  }, [token]);

  useEffect(() => {
    if (!token || !isDev || activeTab !== "dev") return;
    fetchDevStatus(token);
    fetchDevSmoke(token);
  }, [token, isDev, activeTab]);

  useEffect(() => {
    if (!token || !currentUser?.id || tempSignals.length === 0) return;
    const importKey = `${SIGNALS_IMPORTED_PREFIX}${currentUser.id}`;
    if (localStorage.getItem(importKey) === "true") return;
    importTemporarySignals(token, currentUser.id);
  }, [token, currentUser?.id, tempSignals.length]);

  useEffect(() => {
    if (tempSignals.length === 0) {
      localStorage.removeItem(TEMP_SIGNALS_KEY);
      return;
    }
    localStorage.setItem(TEMP_SIGNALS_KEY, JSON.stringify(tempSignals));
    if (tempSignals.length >= 7) localStorage.setItem(ONBOARDING_DONE_KEY, "true");
  }, [tempSignals]);

  async function loadHealth() {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      setApiStatus(response.data.status || "ok");
      setApiVersion(response.data.version || "");
    } catch {
      setApiStatus("offline");
    }
  }

  async function loadOnboardingCards() {
    setLoadingCards(true);
    setCardsError("");
    try {
      const response = await axios.get(`${API_BASE_URL}/cards/onboarding`);
      setOnboardingCards(response.data || []);
    } catch {
      setCardsError("Could not load the first signal cards.");
    } finally {
      setLoadingCards(false);
    }
  }

  async function loadFeedCards() {
    try {
      const response = await axios.get(`${API_BASE_URL}/cards/feed?limit=120`);
      setFeedCards(prepareFeedDeck(response.data || []));
    } catch {
      setFeedCards([]);
    }
  }

  async function fetchCurrentUser(activeToken = token) {
    if (!activeToken) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setCurrentUser(response.data);
    } catch {
      localStorage.removeItem(AUTH_TOKEN_KEY);
      setToken("");
      setCurrentUser(null);
    }
  }

  async function fetchPromiseData(activeToken = token) {
    if (!activeToken) return;
    setPromisesLoading(true);
    setPromisesError("");
    try {
      const [suggestionsResponse, todayResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/promises/suggestions/today`),
        axios.get(`${API_BASE_URL}/promises/today`, {
          headers: { Authorization: `Bearer ${activeToken}` },
        }),
      ]);
      setPromiseSuggestions(suggestionsResponse.data.suggestions || []);
      setTodayPromises(todayResponse.data);
      setSelectedPromiseIds((todayResponse.data.daily_promises || []).map((promise) => promise.template_id).filter(Boolean));
    } catch (error) {
      setPromisesError(parseApiError(error, "Could not load the Forge."));
    } finally {
      setPromisesLoading(false);
    }
  }

  async function fetchInsightStatus(activeToken = token) {
    if (!activeToken) return;
    try {
      const response = await axios.get(`${API_BASE_URL}/insights/status`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setInsightStatus(response.data);
    } catch {
      setInsightStatus(null);
    }
  }

  async function fetchJotSummary(activeToken = token) {
    if (!activeToken) return;
    setJotsLoading(true);
    setJotsError("");
    try {
      const response = await axios.get(`${API_BASE_URL}/jots/summary?limit=5`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setJotSummary(response.data);
    } catch (error) {
      setJotSummary(null);
      setJotsError(parseApiError(error, "Could not load Jots."));
    } finally {
      setJotsLoading(false);
    }
  }

  async function fetchEvolutionSummary(activeToken = token) {
    if (!activeToken) return;
    setEvolutionLoading(true);
    setEvolutionError("");
    try {
      const response = await axios.get(`${API_BASE_URL}/evolution/summary`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setEvolutionSummary(response.data);
    } catch (error) {
      setEvolutionSummary(null);
      setEvolutionError(parseApiError(error, "Could not load Evolution."));
    } finally {
      setEvolutionLoading(false);
    }
  }

  async function fetchDevStatus(activeToken = token) {
    if (!activeToken) return;
    setDevLoading(true);
    setDevError("");
    try {
      const response = await axios.get(`${API_BASE_URL}/dev/status`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setDevStatus(response.data);
    } catch (error) {
      setDevStatus(null);
      setDevError(parseApiError(error, "Dev tools are not available for this user."));
    } finally {
      setDevLoading(false);
    }
  }

  async function fetchDevSmoke(activeToken = token) {
    if (!activeToken) return;
    setDevSmokeLoading(true);
    setDevSmokeError("");
    try {
      const response = await axios.get(`${API_BASE_URL}/dev/smoke`, {
        headers: { Authorization: `Bearer ${activeToken}` },
      });
      setDevSmoke(response.data);
    } catch (error) {
      setDevSmoke(null);
      setDevSmokeError(parseApiError(error, "Could not run the MVP smoke check."));
    } finally {
      setDevSmokeLoading(false);
    }
  }

  async function importTemporarySignals(activeToken = token, userId = currentUser?.id) {
    const signals = getStoredSignals();
    if (!activeToken || !userId || signals.length === 0) return;
    try {
      await axios.post(
        `${API_BASE_URL}/signals/import-onboarding`,
        { signals },
        { headers: { Authorization: `Bearer ${activeToken}` } },
      );
      localStorage.setItem(`${SIGNALS_IMPORTED_PREFIX}${userId}`, "true");
      localStorage.removeItem(TEMP_SIGNALS_KEY);
      localStorage.removeItem(ONBOARDING_DONE_KEY);
      setTempSignals([]);
      await fetchCurrentUser(activeToken);
      await fetchInsightStatus(activeToken);
      await fetchEvolutionSummary(activeToken);
      navigator.vibrate?.(45);
    } catch {
      // Keep the local signals so the user can try again later.
    }
  }

  async function createFeedSignal({ card, choice, direction = "tap", accepted = true, jotText = "" }) {
    if (!token || !card) return;
    setFeedStatus("saving");
    setFeedMessage("");
    try {
      const response = await axios.post(
        `${API_BASE_URL}/signals/card`,
        {
          card_id: card.id,
          choice,
          direction,
          accepted,
          jot_text: jotText || null,
        },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      if (direction === "micro_jot") {
        setFeedMessage("Jot saved. One step off the popular path.");
      } else if (card.type === "challenge" && accepted) {
        setFeedMessage("Challenge added to today’s Forge.");
      } else if (direction === "skip") {
        setFeedMessage("Skipped. The deck moves.");
      } else {
        setFeedMessage(`Signal captured · ${response.data.accepted_signal_count} accepted`);
      }
      setFeedStatus("saved");
      setFeedIndex((index) => index + 1);
      await fetchCurrentUser(token);
      await fetchPromiseData(token);
      await fetchInsightStatus(token);
      await fetchJotSummary(token);
      await fetchEvolutionSummary(token);
      navigator.vibrate?.(35);
    } catch (error) {
      setFeedStatus("error");
      setFeedMessage(parseApiError(error, "Could not save this signal."));
    }
  }

  function goToPreviousFeedCard() {
    setFeedMessage("");
    setFeedStatus("idle");
    setFeedIndex((index) => Math.max(0, index - 1));
    navigator.vibrate?.(18);
  }

  async function handleAuthSubmit(formValues) {
    setAuthLoading(true);
    setAuthError("");
    try {
      const endpoint = authMode === "register" ? "/auth/register" : "/auth/login";
      const payload = authMode === "register"
        ? {
            email: formValues.email,
            password: formValues.password,
            username: formValues.username || null,
            display_name: formValues.displayName || null,
          }
        : { email: formValues.email, password: formValues.password };

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, payload);
      const accessToken = response.data.access_token;
      localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
      setToken(accessToken);
      setAuthMode(null);
      setActiveTab("feed");
      await fetchCurrentUser(accessToken);
      await fetchPromiseData(accessToken);
      await fetchInsightStatus(accessToken);
      await fetchJotSummary(accessToken);
      await fetchEvolutionSummary(accessToken);
      navigator.vibrate?.(30);
    } catch (error) {
      setAuthError(parseApiError(error, "Authentication failed."));
    } finally {
      setAuthLoading(false);
    }
  }

  function logout() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken("");
    setCurrentUser(null);
    setAuthMode(null);
    setActiveTab("feed");
    setFeedStatus("idle");
    setFeedMessage("");
    setJotSummary(null);
    setDevStatus(null);
    setDevError("");
  }

  function resetOnboarding() {
    localStorage.removeItem(TEMP_SIGNALS_KEY);
    localStorage.removeItem(ONBOARDING_DONE_KEY);
    if (currentUser?.id) localStorage.removeItem(`${SIGNALS_IMPORTED_PREFIX}${currentUser.id}`);
    setTempSignals([]);
    setLastOnboardingChoice(null);
  }

  function handleOnboardingChoice(card, choice, direction = "tap") {
    if (!card || onboardingComplete) return;
    const accepted = choice !== "Not for me" && choice !== "Skip" && choice !== "Not now";
    const signal = {
      temporary_id: crypto.randomUUID(),
      card_id: card.id,
      card_type: card.type,
      card_title: card.title,
      choice,
      direction,
      accepted,
      tags: card.tags || [],
      signal_weights: card.signal_weights?.[choice] || {},
      created_at: new Date().toISOString(),
    };
    setTempSignals((current) => [...current, signal]);
    setLastOnboardingChoice({ choice, accepted });
    navigator.vibrate?.(20);
  }

  function togglePromiseSelection(templateId) {
    if (todayPromises?.is_locked) return;
    setPromiseMessage("");
    setSelectedPromiseIds((current) => {
      if (current.includes(templateId)) return current.filter((id) => id !== templateId);
      if (current.length >= 3) return current;
      return [...current, templateId];
    });
  }

  async function selectTodayPromises() {
    if (!token || selectedPromiseIds.length !== 3) return;
    setPromiseMessage("Locking today's Promises...");
    try {
      const response = await axios.post(
        `${API_BASE_URL}/promises/select-today`,
        { template_ids: selectedPromiseIds },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setTodayPromises(response.data);
      setPromiseMessage("The day is set. Now forge it.");
      await fetchEvolutionSummary(token);
      navigator.vibrate?.(45);
    } catch (error) {
      setPromiseMessage(parseApiError(error, "Could not lock today's Promises."));
      await fetchPromiseData(token);
    }
  }

  async function forgeDailyPromise(dailyPromiseId) {
    if (!token || !dailyPromiseId || forgingPromiseId) return;
    setForgingPromiseId(dailyPromiseId);
    setForgeToast(null);
    try {
      const response = await axios.post(
        `${API_BASE_URL}/promises/${dailyPromiseId}/forge`,
        { proof_text: "Forged from the JotPop Forge tab." },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setTodayPromises(response.data.today);
      setForgeToast({ title: "🔥 Promise Forged", body: "The Forge remembers." });
      await fetchCurrentUser(token);
      await fetchEvolutionSummary(token);
      navigator.vibrate?.([35, 25, 55]);
      setTimeout(() => setForgeToast(null), 2600);
    } catch (error) {
      setForgeToast({ title: "Forge missed", body: parseApiError(error, "Could not forge this Promise.") });
      await fetchPromiseData(token);
    } finally {
      setForgingPromiseId(null);
    }
  }

  async function respondToInsight(insightId, accepted) {
    if (!token || !insightId) return;
    try {
      const response = await axios.post(
        `${API_BASE_URL}/insights/${insightId}/respond`,
        { accepted },
        { headers: { Authorization: `Bearer ${token}` } },
      );
      setInsightMessage(response.data.message || "Insight response saved.");
      await fetchInsightStatus(token);
      await fetchEvolutionSummary(token);
    } catch (error) {
      setInsightMessage(parseApiError(error, "Could not save Insight response."));
    }
  }

  return (
    <main className={`app-shell bg-zinc-950 text-white ${isLoggedIn && activeTab === "feed" ? "h-[100dvh] overflow-hidden" : "min-h-screen"}`}>
      <div className={`mx-auto flex w-full max-w-md flex-col px-3 ${isLoggedIn ? "pt-[calc(5.25rem+env(safe-area-inset-top))] pb-[calc(5.75rem+env(safe-area-inset-bottom))]" : "min-h-screen px-4 pb-[calc(6.25rem+env(safe-area-inset-bottom))] pt-[calc(0.75rem+env(safe-area-inset-top))]"} ${isLoggedIn && activeTab === "feed" ? "h-[100dvh] overflow-hidden" : "min-h-screen"}`}> 
        {isLoggedIn ? (
          <TopStatusBar
            character={character}
            todayPromises={todayPromises}
            isDev={isDev}
            onOpenDev={() => setActiveTab("dev")}
            onLogout={logout}
          />
        ) : (
          <PreAuthHeader onSignIn={() => setAuthMode("login")} apiStatus={apiStatus} />
        )}

        <section className={isLoggedIn && activeTab === "feed" ? "flex min-h-0 flex-1 flex-col" : "flex flex-1 flex-col pt-4"}>
          {isLoggedIn ? (
            <>
              {activeTab === "feed" ? (
                <FeedPage
                  cards={feedCards}
                  activeIndex={feedIndex}
                  status={feedStatus}
                  message={feedMessage}
                  onSignal={createFeedSignal}
                  onRestart={() => {
                    setFeedCards((current) => prepareFeedDeck(current));
                    setFeedIndex(0);
                    setFeedStatus("idle");
                    setFeedMessage("");
                  }}
                  onPrevious={goToPreviousFeedCard}
                  insightStatus={insightStatus}
                  onRespondInsight={respondToInsight}
                  insightMessage={insightMessage}
                  jotSummary={jotSummary}
                  jotsLoading={jotsLoading}
                  jotsError={jotsError}
                />
              ) : null}

              {activeTab === "forge" ? (
                <ForgePage
                  suggestions={promiseSuggestions}
                  todayPromises={todayPromises}
                  selectedPromiseIds={selectedPromiseIds}
                  loading={promisesLoading}
                  error={promisesError}
                  message={promiseMessage}
                  onTogglePromise={togglePromiseSelection}
                  onLockPromises={selectTodayPromises}
                  onForgePromise={forgeDailyPromise}
                  forgingPromiseId={forgingPromiseId}
                  onRefresh={() => fetchPromiseData(token)}
                />
              ) : null}

              {activeTab === "evolution" ? (
                <EvolutionPage
                  summary={evolutionSummary}
                  loading={evolutionLoading}
                  error={evolutionError}
                  onRefresh={() => fetchEvolutionSummary(token)}
                  jotSummary={jotSummary}
                />
              ) : null}

              {activeTab === "dev" ? (
                <DevToolsPage
                  status={devStatus}
                  loading={devLoading}
                  error={devError}
                  smoke={devSmoke}
                  smokeLoading={devSmokeLoading}
                  smokeError={devSmokeError}
                  isDev={isDev}
                  onRefresh={() => fetchDevStatus(token)}
                  onRunSmoke={() => fetchDevSmoke(token)}
                  onBack={() => setActiveTab("evolution")}
                />
              ) : null}

              <BottomNavigation activeTab={activeTab} onChange={setActiveTab} />
              <ForgeToast toast={forgeToast} />
            </>
          ) : loadingCards ? (
            <LoadingCard />
          ) : cardsError ? (
            <ErrorCard message={cardsError} onRetry={loadOnboardingCards} />
          ) : onboardingComplete ? (
            <OnboardingGate
              acceptedSignals={tempSignals.filter((signal) => signal.accepted).length}
              totalSignals={tempSignals.length}
              onRestart={resetOnboarding}
              onCreateAccount={() => setAuthMode("register")}
              onSignIn={() => setAuthMode("login")}
            />
          ) : (
            <OnboardingFeed
              card={currentOnboardingCard}
              progress={tempSignals.length + 1}
              total={7}
              lastChoice={lastOnboardingChoice}
              onChoice={handleOnboardingChoice}
            />
          )}
        </section>
      </div>

      <AnimatePresence>
        {authMode ? (
          <AuthModal
            mode={authMode}
            onClose={() => {
              setAuthMode(null);
              setAuthError("");
            }}
            onSwitchMode={() => {
              setAuthError("");
              setAuthMode(authMode === "register" ? "login" : "register");
            }}
            onSubmit={handleAuthSubmit}
            loading={authLoading}
            error={authError}
          />
        ) : null}
      </AnimatePresence>
    </main>
  );
}

function PreAuthHeader({ onSignIn, apiStatus }) {
  return (
    <header className="flex items-center justify-between gap-4 rounded-[1.6rem] border border-white/10 bg-black/25 px-4 py-3 backdrop-blur-xl">
      <div>
        <p className="text-[10px] uppercase tracking-[0.28em] text-cyan-200/70">JotPop</p>
        <h1 className="text-lg font-black">Find your signal.</h1>
      </div>
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${apiStatus === "ok" ? "bg-emerald-300" : "bg-amber-300"}`} />
        <button onClick={onSignIn} className="rounded-full border border-white/10 bg-white/[0.07] px-4 py-2 text-sm font-semibold text-zinc-100">
          Sign in
        </button>
      </div>
    </header>
  );
}

function TopStatusBar({ character, todayPromises, isDev, onOpenDev, onLogout }) {
  const accepted = character?.accepted_signal_count ?? 0;
  const forgeState = todayPromises?.forge_state || character?.forge_state || "Cold";
  const today = todayPromises?.alignment_percent ?? character?.today_alignment ?? 0;
  const state = character?.current_state || "Exploring";

  return (
    <header className="fixed left-1/2 top-0 z-50 w-full max-w-md -translate-x-1/2 px-3 pt-[calc(0.35rem+env(safe-area-inset-top))]">
      <div className="rounded-2xl border border-white/10 bg-zinc-950/82 px-3 py-2 shadow-xl shadow-black/30 backdrop-blur-xl">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-baseline gap-2">
              <p className="text-sm font-black tracking-tight text-white">JotPop</p>
              <span className="truncate text-[11px] font-bold text-zinc-500">{state}</span>
            </div>
            <p className="mt-0.5 truncate text-[11px] font-semibold text-zinc-400">
              {accepted} Signals · {forgeState} · Today {today}%
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-1.5">
            {isDev ? (
              <button onClick={onOpenDev} className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-2.5 py-1.5 text-[10px] font-black text-cyan-100 active:scale-95">
                Dev
              </button>
            ) : null}
            <button onClick={onLogout} className="rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1.5 text-[10px] font-bold text-zinc-400 active:scale-95">
              Exit
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

function StatusChip({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.045] px-2 py-2">
      <p className="text-[9px] uppercase tracking-[0.18em] text-zinc-500">{label}</p>
      <p className="mt-1 truncate text-xs font-black text-white">{value}</p>
    </div>
  );
}

function BottomNavigation({ activeTab, onChange }) {
  const tabs = [
    { id: "feed", label: "Feed", icon: "✦" },
    { id: "forge", label: "Forge", icon: "🔥" },
    { id: "evolution", label: "Evolution", icon: "◇" },
  ];

  return (
    <nav className="fixed bottom-0 left-1/2 z-50 w-full max-w-md -translate-x-1/2 px-3 pb-[calc(0.45rem+env(safe-area-inset-bottom))]">
      <div className="grid grid-cols-3 gap-1 rounded-2xl border border-white/10 bg-zinc-950/86 p-1.5 shadow-xl shadow-black/50 backdrop-blur-xl">
        {tabs.map((tab) => {
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onChange(tab.id)}
              className={`rounded-xl px-2 py-2.5 text-center transition active:scale-[0.97] ${active ? "bg-white text-zinc-950" : "text-zinc-400"}`}
            >
              <span className="mr-1 text-sm leading-none">{tab.icon}</span>
              <span className="text-[12px] font-black">{tab.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function OnboardingFeed({ card, progress, total, lastChoice, onChoice }) {
  return (
    <div className="flex flex-1 flex-col justify-center gap-4">
      <div>
        <p className="text-xs uppercase tracking-[0.24em] text-zinc-500">First signals</p>
        <h2 className="mt-2 text-3xl font-black leading-tight">No account yet. Just choose.</h2>
        <p className="mt-3 text-sm leading-6 text-zinc-400">Seven quick signals open the gate.</p>
      </div>
      <SignalCard card={card} progress={progress} total={total} onChoice={onChoice} mode="onboarding" />
      {lastChoice ? <Notice tone={lastChoice.accepted ? "success" : "info"}>{lastChoice.accepted ? "Signal captured." : "Not now. The deck shifts."}</Notice> : null}
    </div>
  );
}

function FeedPage({ cards, activeIndex, status, message, onSignal, onRestart, onPrevious }) {
  const complete = cards.length > 0 && activeIndex >= cards.length;

  return (
    <div className="feed-screen relative flex min-h-0 flex-1 overflow-hidden">
      {complete ? (
        <section className="my-auto w-full rounded-[2rem] border border-emerald-300/20 bg-emerald-500/10 p-6 text-center">
          <p className="text-xs uppercase tracking-[0.24em] text-emerald-200">Deck complete</p>
          <h3 className="mt-3 text-2xl font-black">The current deck became signals.</h3>
          <p className="mt-3 text-sm leading-6 text-zinc-300">Shuffle it again or come back when the next deck evolves.</p>
          <button onClick={onRestart} className="mt-5 w-full rounded-2xl bg-white px-4 py-4 font-black text-zinc-950 active:scale-[0.98]">
            Shuffle again
          </button>
        </section>
      ) : (
        <VisibleCardStack cards={cards} activeIndex={activeIndex} onSignal={onSignal} onPrevious={onPrevious} status={status} />
      )}
      <FeedToast message={message} status={status} />
    </div>
  );
}

function JotTrailPanel({ summary, loading, error }) {
  const [openJotId, setOpenJotId] = useState(null);
  const latest = summary?.latest_jots || [];
  const total = summary?.total_jots ?? 0;
  const pathMessage = summary?.path_message || "No Jots yet. The deck is still mostly generic.";

  return (
    <section className="jot-trail-card rounded-[1.7rem] border border-fuchsia-300/18 bg-fuchsia-500/8 p-4 shadow-xl shadow-fuchsia-500/5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-[0.24em] text-fuchsia-200/80">Jot trail</p>
          <h3 className="mt-1 text-lg font-black">Off the popular path</h3>
        </div>
        <span className="rounded-full border border-fuchsia-300/20 bg-fuchsia-500/10 px-3 py-1 text-xs font-black text-fuchsia-100">{total}</span>
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-400">{pathMessage}</p>
      {loading ? <p className="mt-3 text-sm text-zinc-500">Loading Jots...</p> : null}
      {error ? <p className="mt-3 text-sm text-amber-200">{error}</p> : null}
      {latest.length ? (
        <div className="mt-3 grid gap-2">
          {latest.slice(0, 3).map((jot) => {
            const open = openJotId === jot.id;
            return (
              <button
                key={jot.id}
                type="button"
                onClick={() => setOpenJotId((current) => current === jot.id ? null : jot.id)}
                className="rounded-2xl border border-white/10 bg-black/24 p-3 text-left transition active:scale-[0.98]"
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="truncate text-xs font-bold uppercase tracking-[0.16em] text-zinc-500">{jot.prompt || "Micro-Jot"}</span>
                  <span className="text-[10px] font-bold text-fuchsia-100">{open ? "Hide" : "Reveal"}</span>
                </div>
                <AnimatePresence initial={false}>
                  {open ? (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 overflow-hidden text-sm leading-6 text-zinc-200"
                    >
                      “{jot.content}”
                    </motion.p>
                  ) : null}
                </AnimatePresence>
              </button>
            );
          })}
        </div>
      ) : (
        <p className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-sm leading-6 text-zinc-500">Rare Micro-Jots will appear here. For now, the deck is learning mostly from taps and swipes.</p>
      )}
    </section>
  );
}

function VisibleCardStack({ cards, activeIndex, onSignal, onPrevious, status }) {
  const visible = [cards[activeIndex], cards[activeIndex + 1], cards[activeIndex + 2]].filter(Boolean);

  if (!visible.length) return <SmallEmptyState text="No feed card available." />;

  return (
    <div className="relative h-full w-full min-h-0 overflow-hidden pt-1">
      {visible.slice().reverse().map((card, reversedIndex) => {
        const stackIndex = visible.length - 1 - reversedIndex;
        const isTop = stackIndex === 0;
        return (
          <motion.div
            key={card.id}
            className="absolute inset-x-0 top-2 bottom-2"
            style={{ zIndex: 10 - stackIndex }}
            animate={{
              y: stackIndex * 14,
              scale: 1 - stackIndex * 0.045,
              opacity: 1 - stackIndex * 0.28,
            }}
            transition={{ type: "spring", stiffness: 260, damping: 28 }}
          >
            {isTop ? (
              <SignalCard card={card} progress={activeIndex + 1} total={cards.length} onChoice={(activeCard, choice, direction, extra = {}) => onSignal({ card: activeCard, choice, direction, ...extra })} onPrevious={onPrevious} mode="feed" saving={status === "saving"} />
            ) : (
              <CardBack card={card} />
            )}
          </motion.div>
        );
      })}
    </div>
  );
}

function CardBack({ card }) {
  const theme = themeMap[card?.visual_theme] || themeMap.signal;
  return (
    <article className={`h-full rounded-[2rem] border ${theme.border} bg-gradient-to-br ${theme.shell} shadow-xl ${theme.glow}`}>
      <div className="h-full rounded-[2rem] bg-black/25" />
    </article>
  );
}

function SignalCard({ card, progress, total, onChoice, onPrevious, mode, saving = false }) {
  const [jotText, setJotText] = useState("");
  const [jotWarning, setJotWarning] = useState("");
  const [shakeKey, setShakeKey] = useState(0);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [jotFocused, setJotFocused] = useState(false);
  const jotTouchStartRef = useRef(null);
  const theme = themeMap[card?.visual_theme] || themeMap.signal;
  const options = Array.isArray(card?.options) ? card.options : [];
  const isBinary = options.length === 2 || card?.type === "this_or_that" || card?.type === "swipe";
  const isMicroJot = card?.type === "micro_jot";
  const isChallenge = card?.type === "challenge";
  const isFeed = mode === "feed";
  const progressPercent = total ? Math.min(100, Math.round((progress / total) * 100)) : 0;
  const isEmptyJot = isMicroJot && !jotText.trim();
  const canDrag = isFeed && !saving && !(isMicroJot && jotFocused && !isEmptyJot) && !detailsOpen;

  if (!card) return <SmallEmptyState text="No card loaded." />;

  function choose(choice, direction = "tap", extra = {}) {
    if (saving) return;
    onChoice(card, choice, direction, extra);
  }

  function skip() {
    choose("Skipped", "skip", { accepted: false });
  }

  function goBack() {
    if (mode !== "feed" || !onPrevious) return;
    onPrevious();
  }

  function keepEditing() {
    if (isMicroJot) {
      setJotWarning("Keep shaping it. Swipe right only when it feels yours.");
    }
    setShakeKey((value) => value + 1);
    navigator.vibrate?.(15);
  }

  function handleEmptyJotTouchStart(event) {
    if (!isMicroJot || jotText.trim() || saving) return;
    const touch = event.touches?.[0];
    if (!touch) return;
    jotTouchStartRef.current = { x: touch.clientX, y: touch.clientY };
  }

  function handleEmptyJotTouchEnd(event) {
    if (!isMicroJot || jotText.trim() || saving || !jotTouchStartRef.current) return;
    const touch = event.changedTouches?.[0];
    if (!touch) return;
    const start = jotTouchStartRef.current;
    jotTouchStartRef.current = null;
    const deltaX = touch.clientX - start.x;
    const deltaY = touch.clientY - start.y;
    const absX = Math.abs(deltaX);
    const absY = Math.abs(deltaY);

    if (deltaY < -70 && absY > absX * 1.15) {
      event.preventDefault();
      event.currentTarget.blur();
      setJotFocused(false);
      setJotWarning("");
      skip();
    }
  }

  function handleCardDragEnd(_, info) {
    if (!canDrag) return;
    const { x, y } = info.offset;
    const { x: velocityX, y: velocityY } = info.velocity;
    const absX = Math.abs(x);
    const absY = Math.abs(y);
    const horizontalIntent = absX > absY && (absX > 82 || Math.abs(velocityX) > 500);
    const verticalIntent = absY >= absX && (absY > 82 || Math.abs(velocityY) > 500);

    if (verticalIntent && y < 0) {
      skip();
      return;
    }

    if (verticalIntent && y > 0) {
      goBack();
      return;
    }

    if (!horizontalIntent) return;

    if (isMicroJot) {
      if (x > 0) saveJot();
      else keepEditing();
      return;
    }

    if (isChallenge) {
      if (x > 0) choose("Accept challenge", "right", { accepted: true });
      else choose("Not for me", "left", { accepted: false });
      return;
    }

    if (isBinary && options.length >= 2) {
      const index = x < 0 ? 0 : 1;
      const option = options[index];
      choose(option, index === 0 ? "left" : "right", { accepted: option !== "Not for me" });
    }
  }

  function saveJot() {
    const trimmed = jotText.trim();
    if (!trimmed) {
      setJotWarning("Write a Jot first.");
      setShakeKey((value) => value + 1);
      navigator.vibrate?.(25);
      return;
    }
    if (trimmed.length > 140) {
      setJotWarning("Keep it under 140 characters.");
      setShakeKey((value) => value + 1);
      return;
    }
    choose("submitted", "micro_jot", { accepted: true, jotText: trimmed });
    setJotText("");
  }

  return (
    <motion.article
      key={`${card.id}-${shakeKey}`}
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      animate={jotWarning ? { opacity: 1, y: 0, scale: 1, x: [0, -8, 8, -4, 4, 0] } : { opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -24, scale: 0.96 }}
      transition={{ duration: jotWarning ? 0.38 : 0.22 }}
      drag={canDrag}
      dragConstraints={{ left: 0, right: 0, top: 0, bottom: 0 }}
      dragElastic={0.32}
      whileDrag={{ scale: 1.018, rotate: isMicroJot ? 0 : 1.2 }}
      onDragEnd={handleCardDragEnd}
      className={`relative flex h-full touch-none flex-col overflow-hidden rounded-[2rem] border ${theme.border} bg-gradient-to-br ${theme.shell} p-4 shadow-2xl ${theme.glow}`}
    >
      {mode === "feed" ? <GestureCompass isBinary={isBinary} isMicroJot={isMicroJot} isFocused={jotFocused} /> : null}
      <div className="absolute -right-24 -top-24 h-56 w-56 rounded-full bg-white/10 blur-3xl" />
      <div className="relative z-10 flex min-h-0 flex-1 flex-col">
        <div className="mb-2 flex items-center justify-between gap-3">
          <span className={`rounded-full px-2.5 py-1 text-[10px] font-black ${theme.chip}`}>{card.icon || "✦"} {formatCardType(card.type)}</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onPointerDown={(event) => event.stopPropagation()}
              onClick={() => setDetailsOpen(true)}
              className="rounded-full border border-white/10 bg-black/20 px-2.5 py-1 text-[10px] font-black uppercase tracking-[0.14em] text-zinc-300 active:scale-95"
            >
              More
            </button>
            <span className="text-[11px] font-semibold text-zinc-500">{progress}/{total}</span>
          </div>
        </div>

        <div className="mb-4 h-1 overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full bg-white/70" style={{ width: `${progressPercent}%` }} />
        </div>

        <div className="flex min-h-0 flex-1 flex-col justify-center py-2">
          <h2 className="text-[clamp(1.65rem,7vw,2.45rem)] font-black leading-[0.98] tracking-tight">{card.title}</h2>
          {card.subtitle ? <p className="mt-4 line-clamp-3 text-sm leading-6 text-zinc-300">{card.subtitle}</p> : null}

          {isMicroJot ? (
            <div className="mt-5">
              <textarea
                value={jotText}
                onPointerDown={(event) => {
                  if (jotText.trim()) event.stopPropagation();
                }}
                onTouchStart={handleEmptyJotTouchStart}
                onTouchEnd={handleEmptyJotTouchEnd}
                onFocus={() => {
                  setJotFocused(true);
                  setJotWarning("");
                }}
                onBlur={() => setJotFocused(false)}
                onChange={(event) => {
                  setJotText(event.target.value.slice(0, 160));
                  setJotWarning("");
                }}
                placeholder="Write the sentence only you would write."
                className="h-32 w-full resize-none rounded-[1.35rem] border border-white/10 bg-black/35 p-4 text-base leading-6 text-white outline-none placeholder:text-zinc-600 focus:border-cyan-200/40"
              />
              <div className="mt-2 flex items-center justify-between gap-3 text-[11px] font-semibold text-zinc-500">
                <span>{jotFocused ? (jotText.trim() ? "Finish the thought." : "Swipe up to pass.") : "Swipe right to save · up to pass"}</span>
                <span className={jotText.length > 140 ? "text-red-200" : ""}>{jotText.length}/140</span>
              </div>
              {jotWarning ? <p className="mt-3 text-sm font-semibold text-amber-200">{jotWarning}</p> : null}
            </div>
          ) : isChallenge ? (
            <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-black/20 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-zinc-500">Challenge card</p>
              <p className="mt-2 text-sm leading-6 text-zinc-300">Swipe right to accept. Swipe left if it is not yours today.</p>
            </div>
          ) : isBinary ? (
            <div className="mt-6 grid grid-cols-2 gap-3">
              {options.slice(0, 2).map((option, index) => (
                <button
                  key={option}
                  type="button"
                  onPointerDown={(event) => event.stopPropagation()}
                  onClick={() => choose(option, index === 0 ? "left" : "right", { accepted: option !== "Not for me" })}
                  disabled={saving}
                  className="min-h-24 rounded-[1.45rem] border border-white/10 bg-black/25 p-3 text-left font-black text-white active:scale-[0.98] disabled:opacity-60"
                >
                  <span className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">{index === 0 ? "Left" : "Right"}</span>
                  <span className="mt-2 block text-base leading-5">{option}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="mt-5 grid gap-2.5">
              {options.slice(0, 4).map((option) => (
                <button key={option} type="button" onPointerDown={(event) => event.stopPropagation()} onClick={() => choose(option, "tap", { accepted: true })} disabled={saving} className="rounded-[1.25rem] border border-white/10 bg-black/25 px-4 py-3 text-left text-sm font-bold text-white active:scale-[0.98] disabled:opacity-60">
                  {option}
                </button>
              ))}
            </div>
          )}
        </div>

        {mode === "feed" ? (
          <div className="mt-2 flex items-center justify-center text-[10px] font-bold uppercase tracking-[0.18em] text-zinc-600">
            swipe the card
          </div>
        ) : null}
      </div>

      <AnimatePresence>
        {detailsOpen ? <CardDetailSheet card={card} onClose={() => setDetailsOpen(false)} /> : null}
      </AnimatePresence>
    </motion.article>
  );
}

function CardDetailSheet({ card, onClose }) {
  const tags = Array.isArray(card?.tags) ? card.tags : [];
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-40 bg-black/45 backdrop-blur-sm"
      onPointerDown={(event) => event.stopPropagation()}
    >
      <motion.div
        initial={{ y: "100%" }}
        animate={{ y: 0 }}
        exit={{ y: "100%" }}
        transition={{ type: "spring", stiffness: 280, damping: 30 }}
        className="absolute inset-x-3 bottom-3 top-16 overflow-y-auto rounded-[1.65rem] border border-white/10 bg-zinc-950/96 p-4 shadow-2xl"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-200/75">Card depth</p>
            <h3 className="mt-1 text-xl font-black">{card?.title}</h3>
          </div>
          <button onClick={onClose} className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-xs font-black text-zinc-300 active:scale-95">Close</button>
        </div>
        {card?.subtitle ? <p className="mt-4 text-sm leading-6 text-zinc-300">{card.subtitle}</p> : null}
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4">
          <p className="text-[10px] uppercase tracking-[0.18em] text-zinc-500">Why it matters</p>
          <p className="mt-2 text-sm leading-6 text-zinc-400">This is optional depth. The main Feed stays fast; this panel is only here when you want more context before you swipe.</p>
        </div>
        {tags.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {tags.map((tag) => <span key={tag} className="rounded-full border border-white/10 bg-black/25 px-3 py-1.5 text-xs font-semibold text-zinc-300">#{tag}</span>)}
          </div>
        ) : null}
      </motion.div>
    </motion.div>
  );
}

function FeedToast({ message, status }) {
  return (
    <AnimatePresence>
      {message ? (
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 16 }}
          className={`pointer-events-none absolute inset-x-4 bottom-4 z-30 rounded-2xl border px-4 py-3 text-center text-sm font-black shadow-xl backdrop-blur-xl ${status === "error" ? "border-red-300/25 bg-red-500/20 text-red-100" : "border-cyan-300/20 bg-zinc-950/75 text-cyan-100"}`}
        >
          {message}
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function GestureCompass({ isBinary, isMicroJot, isFocused }) {
  return (
    <div className="pointer-events-none absolute inset-0 z-20">
      <div className="absolute left-1/2 top-2 -translate-x-1/2 rounded-full border border-white/10 bg-black/22 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-zinc-500">
        ↑ next
      </div>
      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full border border-white/10 bg-black/22 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-zinc-600">
        ↓ previous
      </div>
      {isMicroJot ? (
        <>
          <div className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-black/22 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-zinc-600">← edit</div>
          <div className={`absolute right-2 top-1/2 -translate-y-1/2 rounded-full border px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.16em] ${isFocused ? "border-white/10 bg-black/22 text-zinc-500" : "border-cyan-200/20 bg-cyan-500/10 text-cyan-100"}`}>{isFocused ? "finish" : "save →"}</div>
        </>
      ) : isBinary ? (
        <>
          <div className="absolute left-2 top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-black/22 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-zinc-600">← left</div>
          <div className="absolute right-2 top-1/2 -translate-y-1/2 rounded-full border border-white/10 bg-black/22 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.16em] text-zinc-500">right →</div>
        </>
      ) : null}
    </div>
  );
}

function SwipeRail({ label, icon, onComplete, disabled }) {
  const [dragX, setDragX] = useState(0);

  function complete() {
    if (disabled) return;
    setDragX(0);
    onComplete();
  }

  return (
    <div className="mt-4">
      <div className="relative h-16 overflow-hidden rounded-2xl border border-cyan-300/20 bg-gradient-to-r from-zinc-950 via-cyan-950/40 to-cyan-400/20">
        <div className="absolute inset-0 flex items-center justify-center text-sm font-bold text-cyan-100/80">{label}</div>
        <motion.button
          type="button"
          drag={disabled ? false : "x"}
          dragConstraints={{ left: 0, right: 220 }}
          dragElastic={0.08}
          onDrag={(_, info) => setDragX(Math.max(0, info.offset.x))}
          onDragEnd={(_, info) => {
            if (info.offset.x > 130 || info.velocity.x > 650) complete();
            else setDragX(0);
          }}
          animate={{ x: dragX }}
          transition={{ type: "spring", stiffness: 420, damping: 32 }}
          disabled={disabled}
          className="absolute left-2 top-2 grid h-12 w-12 place-items-center rounded-xl border border-white/15 bg-white text-xl shadow-lg shadow-cyan-500/20 disabled:opacity-60"
          aria-label={label}
        >
          {icon}
        </motion.button>
      </div>
    </div>
  );
}

function InsightCard({ insight, message, onRespond }) {
  return (
    <section className="rounded-[2rem] border border-amber-300/25 bg-gradient-to-br from-amber-500/15 via-black/25 to-violet-500/10 p-5 shadow-xl shadow-amber-500/10">
      <p className="text-xs uppercase tracking-[0.24em] text-amber-200">✨ Insight unlocked</p>
      <h3 className="mt-3 text-2xl font-black">{insight.title}</h3>
      <p className="mt-3 text-sm leading-6 text-zinc-300">{insight.content}</p>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <button onClick={() => onRespond(insight.id, false)} className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 font-bold text-zinc-200 active:scale-[0.98]">Not me</button>
        <button onClick={() => onRespond(insight.id, true)} className="rounded-2xl bg-amber-200 px-4 py-4 font-black text-zinc-950 active:scale-[0.98]">Resonates</button>
      </div>
      {message ? <p className="mt-3 text-sm font-semibold text-amber-100">{message}</p> : null}
    </section>
  );
}

function ForgePage({ suggestions, todayPromises, selectedPromiseIds, loading, error, message, onTogglePromise, onLockPromises, onForgePromise, forgingPromiseId, onRefresh }) {
  const dailyPromises = todayPromises?.daily_promises || [];
  const isLocked = Boolean(todayPromises?.is_locked);
  const lockedPromises = [...dailyPromises].sort((a, b) => Number(a.completed) - Number(b.completed));
  const feedChallengeCount = isLocked ? 0 : dailyPromises.filter((promise) => !promise.template_id).length;
  const selectedCount = isLocked ? dailyPromises.length : Math.min(3, feedChallengeCount + selectedPromiseIds.length);
  const remainingToLock = Math.max(0, 3 - selectedCount);
  const completedCount = todayPromises?.completed_count ?? 0;
  const totalForgePoints = todayPromises?.total_forge_points ?? 0;
  const completedForgePoints = todayPromises?.completed_forge_points ?? 0;
  const alignmentPercent = todayPromises?.alignment_percent ?? 0;
  const alignmentLabel = todayPromises?.alignment_label || "Unchosen";
  const forgeState = todayPromises?.forge_state || "Cold";
  const forgeActive = Boolean(todayPromises?.forge_active_today);
  const pointsNeeded = todayPromises?.forge_points_needed_today ?? 2;
  const remainingPoints = Math.max(0, totalForgePoints - completedForgePoints);
  const forgeProgress = totalForgePoints ? Math.min(100, Math.round((completedForgePoints / totalForgePoints) * 100)) : 0;
  const thresholdProgress = Math.min(100, Math.round((Math.min(completedForgePoints, 2) / 2) * 100));

  return (
    <div className="space-y-4">
      <PageTitle
        eyebrow="Forge"
        title={isLocked ? "Forge the day." : "Choose what matters."}
        body={isLocked ? "Today is already shaped. Now turn the promises into proof." : "Pick exactly 3 Promises. Feed challenges can claim one of the first slots."}
      />

      <ForgeHero
        isLocked={isLocked}
        forgeState={forgeState}
        forgeActive={forgeActive}
        completedForgePoints={completedForgePoints}
        totalForgePoints={totalForgePoints}
        thresholdProgress={thresholdProgress}
        forgeProgress={forgeProgress}
        pointsNeeded={pointsNeeded}
        alignmentPercent={alignmentPercent}
        alignmentLabel={alignmentLabel}
        completedCount={completedCount}
        selectedCount={selectedCount}
        remainingPoints={remainingPoints}
      />

      {loading ? <Notice tone="info">Loading Forge...</Notice> : null}
      {error ? <Notice tone="error">{error}</Notice> : null}
      {message ? <Notice tone="info">{message}</Notice> : null}

      {isLocked ? (
        <section className="grid gap-3">
          <div className="flex items-end justify-between gap-3 px-1">
            <div>
              <p className="text-xs uppercase tracking-[0.24em] text-orange-200/80">Today’s Forge</p>
              <h3 className="mt-1 text-xl font-black">Swipe to Forge</h3>
            </div>
            <span className="rounded-full border border-orange-300/20 bg-orange-500/10 px-3 py-1 text-xs font-bold text-orange-100">{completedCount}/{lockedPromises.length || 3} done</span>
          </div>

          {lockedPromises.length ? lockedPromises.map((promise) => (
            <PromiseCard key={promise.id} promise={promise} loading={forgingPromiseId === promise.id} disabled={Boolean(forgingPromiseId)} onForge={() => onForgePromise(promise.id)} />
          )) : <SmallEmptyState text="No locked Promises found for today." />}
        </section>
      ) : (
        <section className="grid gap-3">
          <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.045] p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-amber-200/80">Before the Forge</p>
                <h3 className="mt-1 text-xl font-black">Choose exactly 3</h3>
              </div>
              <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1 text-sm font-black text-white">{selectedCount}/3</span>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-amber-200 transition-all" style={{ width: `${Math.min(100, (selectedCount / 3) * 100)}%` }} />
            </div>
          </div>

          {feedChallengeCount ? (
            <div className="rounded-[1.45rem] border border-cyan-300/20 bg-cyan-400/8 p-4">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-cyan-100/80">Already added from Feed</p>
              <div className="mt-3 grid gap-2">
                {dailyPromises.filter((promise) => !promise.template_id).map((promise) => (
                  <div key={promise.id} className="rounded-2xl border border-white/10 bg-black/25 px-4 py-3">
                    <p className="font-black text-white">{promise.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.16em] text-zinc-500">Feed challenge · {promise.forge_points} FP</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {suggestions.map((promise) => {
            const selected = selectedPromiseIds.includes(promise.id);
            const disabled = !selected && selectedCount >= 3;
            return (
              <SuggestionPromiseButton
                key={promise.id}
                promise={promise}
                selected={selected}
                disabled={disabled || loading}
                onClick={() => onTogglePromise(promise.id)}
              />
            );
          })}

          <button onClick={onLockPromises} disabled={selectedCount !== 3} className="rounded-2xl bg-white px-4 py-4 font-black text-zinc-950 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45">
            {selectedCount === 3 ? "Lock today’s 3 Promises" : `Choose ${remainingToLock} more`}
          </button>
          <button onClick={onRefresh} className="rounded-2xl px-4 py-3 text-sm font-semibold text-zinc-400">Refresh Promises</button>
        </section>
      )}
    </div>
  );
}

function ForgeHero({ isLocked, forgeState, forgeActive, completedForgePoints, totalForgePoints, thresholdProgress, forgeProgress, pointsNeeded, alignmentPercent, alignmentLabel, completedCount, selectedCount, remainingPoints }) {
  return (
    <section className={`relative overflow-hidden rounded-[2rem] border p-5 shadow-2xl ${forgeActive ? "border-orange-300/35 bg-orange-500/13 shadow-orange-500/15" : "border-orange-300/18 bg-white/[0.045] shadow-black/25"}`}>
      <div className="forge-hero-glow" />
      <div className="relative z-10 flex items-start gap-4">
        <div className={`forge-core ${forgeActive ? "forge-core-lit" : ""}`}>
          <span className="flame-pulse text-3xl">🔥</span>
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-xs uppercase tracking-[0.24em] text-orange-200/80">{isLocked ? "Ritual state" : "Promise ritual"}</p>
          <h3 className="mt-2 text-2xl font-black leading-tight">{isLocked ? (forgeActive ? "Forge lit." : "The Forge waits.") : "The day is unshaped."}</h3>
          <p className="mt-2 text-sm leading-6 text-zinc-300">
            {isLocked
              ? forgeActive
                ? "You showed up today. Keep forging to align the day."
                : `${pointsNeeded} Forge ${pointsNeeded === 1 ? "Point" : "Points"} needed to light today.`
              : "Select the three promises that deserve your attention today."}
          </p>
        </div>
      </div>

      <div className="relative z-10 mt-5 grid grid-cols-2 gap-3">
        <InfoTile label="Forge" value={forgeState} />
        <InfoTile label="Promises" value={isLocked ? `${completedCount}/3` : `${selectedCount}/3`} />
        <InfoTile label="Points" value={isLocked ? `${completedForgePoints}/${totalForgePoints}` : "Choose 3"} />
        <InfoTile label="Alignment" value={`${alignmentPercent}%`} />
      </div>

      {isLocked ? (
        <div className="relative z-10 mt-5 grid gap-3">
          <div>
            <div className="flex justify-between text-[11px] uppercase tracking-[0.18em] text-zinc-500">
              <span>Light threshold</span>
              <span>{Math.min(completedForgePoints, 2)}/2 FP</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-orange-200 transition-all" style={{ width: `${thresholdProgress}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-[11px] uppercase tracking-[0.18em] text-zinc-500">
              <span>Full alignment</span>
              <span>{remainingPoints} FP left</span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-emerald-200 transition-all" style={{ width: `${forgeProgress}%` }} />
            </div>
          </div>
          <p className="rounded-2xl border border-white/10 bg-black/25 px-4 py-3 text-sm font-semibold text-zinc-300">{alignmentLabel}. Forge the promises that still matter.</p>
        </div>
      ) : null}
    </section>
  );
}

function SuggestionPromiseButton({ promise, selected, disabled, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`rounded-[1.5rem] border p-4 text-left transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45 ${selected ? "border-amber-300/50 bg-amber-400/15" : "border-white/10 bg-white/[0.055]"}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="font-black text-white">{promise.title}</p>
          <p className="mt-1 line-clamp-2 text-sm leading-6 text-zinc-400">{promise.description}</p>
        </div>
        <span className={`shrink-0 rounded-full border px-3 py-1 text-xs font-bold ${difficultyClass(promise.difficulty)}`}>{promise.forge_points} FP</span>
      </div>
      <p className={`mt-3 text-sm font-semibold ${selected ? "text-amber-100" : "text-zinc-500"}`}>{selected ? "✓ Chosen" : disabled ? "3 already chosen" : "Tap to choose"}</p>
    </button>
  );
}

function PromiseCard({ promise, loading, disabled, onForge }) {
  const [ritualActive, setRitualActive] = useState(false);
  const [impactActive, setImpactActive] = useState(false);
  const forged = Boolean(promise.completed);
  const ritualVisible = ritualActive || forged;

  function startForgeRitual() {
    if (disabled || loading || forged || ritualActive) return;
    setRitualActive(true);
    setImpactActive(false);
    navigator.vibrate?.([22, 18, 48]);

    window.setTimeout(() => {
      setImpactActive(true);
      navigator.vibrate?.([35, 25, 55]);
    }, 420);

    window.setTimeout(() => {
      onForge();
    }, 760);

    window.setTimeout(() => {
      setRitualActive(false);
      setImpactActive(false);
    }, 2050);
  }

  return (
    <article
      className={`promise-forge-card relative overflow-hidden rounded-[1.7rem] border p-4 transition ${ritualVisible ? "promise-forge-card-lit border-orange-300/40 bg-orange-500/12" : "border-amber-300/20 bg-white/[0.045]"} ${impactActive ? "impact-shake" : ""}`}
    >
      <div className="forge-card-flare" />
      {ritualActive ? <ForgeSparks /> : null}
      <div className="relative z-10 flex items-start justify-between gap-3">
        <div>
          <p className="font-black text-white">{promise.title}</p>
          <p className="mt-2 text-xs uppercase tracking-[0.18em] text-zinc-500">{promise.difficulty} · {promise.forge_points} Forge {promise.forge_points === 1 ? "Point" : "Points"}</p>
        </div>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${forged ? "border-orange-300/30 bg-orange-500/15 text-orange-100" : ritualActive ? "border-amber-200/35 bg-amber-300/15 text-amber-100" : "border-white/10 bg-white/[0.06] text-zinc-300"}`}>{forged ? "🔥 Forged" : ritualActive ? "Forging" : "Locked"}</span>
      </div>
      {forged ? (
        <div className="relative z-10 mt-4 rounded-2xl border border-orange-300/20 bg-black/20 px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-orange-100">The Forge remembers.</p>
            <span className="forged-flame text-xl">🔥</span>
          </div>
        </div>
      ) : (
        <SwipeToForgeButton disabled={disabled || ritualActive} loading={loading} ritualActive={ritualActive} impactActive={impactActive} onForge={startForgeRitual} />
      )}
    </article>
  );
}

function SwipeToForgeButton({ disabled, loading, ritualActive, impactActive, onForge }) {
  const [dragX, setDragX] = useState(0);
  const fillWidth = ritualActive ? 100 : Math.min(100, Math.round((dragX / 220) * 100));

  function triggerForge() {
    if (disabled || loading || ritualActive) return;
    setDragX(0);
    onForge();
  }

  return (
    <div className="mt-4">
      <div className={`forge-rail ritual-rail relative h-18 overflow-hidden rounded-2xl border border-orange-300/25 bg-gradient-to-r from-zinc-950 via-orange-950/40 to-amber-500/20 ${impactActive ? "ritual-impact" : ""}`}>
        <div className="forge-rail-fill" style={{ width: `${fillWidth}%` }} />
        <div className="forge-rail-embers" />
        <div className="absolute inset-0 flex items-center justify-center text-sm font-black text-orange-100/85">{loading || ritualActive ? "Forging..." : "→ Swipe to Forge"}</div>
        <div className="forge-impact-target">
          <span className="flame-pulse text-2xl">🔥</span>
        </div>
        <motion.button
          type="button"
          drag={disabled || loading || ritualActive ? false : "x"}
          dragConstraints={{ left: 0, right: 220 }}
          dragElastic={0.08}
          onDrag={(_, info) => setDragX(Math.max(0, info.offset.x))}
          onDragEnd={(_, info) => {
            if (info.offset.x > 130 || info.velocity.x > 650) triggerForge();
            else setDragX(0);
          }}
          animate={{ x: loading || ritualActive ? 220 : dragX, rotate: ritualActive ? [0, -8, 12, -4, 0] : 0 }}
          transition={{ type: "spring", stiffness: 420, damping: 32 }}
          disabled={disabled || loading || ritualActive}
          className="forge-hammer absolute left-2 top-2 grid h-12 w-12 place-items-center rounded-xl border border-white/15 bg-white text-2xl shadow-lg shadow-orange-500/20 disabled:opacity-80"
          aria-label="Swipe to Forge this Promise"
        >
          🔨
        </motion.button>
      </div>
      {ritualActive ? <p className="mt-3 text-center text-xs font-black uppercase tracking-[0.22em] text-orange-200">Impact forming</p> : null}
    </div>
  );
}

function ForgeSparks() {
  return (
    <div className="pointer-events-none absolute inset-0 z-20 overflow-hidden">
      <span className="forge-spark forge-spark-a">✦</span>
      <span className="forge-spark forge-spark-b">✧</span>
      <span className="forge-spark forge-spark-c">✦</span>
      <span className="forge-spark forge-spark-d">✧</span>
      <span className="forge-spark forge-spark-e">✦</span>
    </div>
  );
}

function ForgeToast({ toast }) {
  return (
    <AnimatePresence>
      {toast ? (
        <motion.div
          initial={{ opacity: 0, y: 26, scale: 0.94 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.96 }}
          className="forge-toast fixed inset-x-4 top-28 z-50 mx-auto max-w-sm rounded-[1.9rem] border border-orange-300/35 bg-zinc-950/94 p-5 text-center shadow-2xl shadow-orange-500/25 backdrop-blur-xl impact-shake"
        >
          <div className="toast-flame mx-auto">🔥</div>
          <p className="mt-3 text-2xl font-black text-orange-100">{toast.title}</p>
          <p className="mt-2 text-sm font-semibold text-zinc-300">{toast.body}</p>
          <div className="spark spark-one">✦</div>
          <div className="spark spark-two">✧</div>
          <div className="spark spark-three">✦</div>
          <div className="spark spark-four">✧</div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

function EvolutionPage({ summary, loading, error, onRefresh, jotSummary }) {
  const character = summary?.character;
  const achievements = summary?.achievements || [];
  const cardTypes = summary?.unlocked_card_types || [];
  const insights = summary?.insights || [];
  const nextUnlock = summary?.next_unlock || {};
  const unlockedCount = achievements.filter((item) => item.unlocked).length;
  const [openAchievementCode, setOpenAchievementCode] = useState(null);

  const patternAxes = useMemo(() => buildPatternAxes(summary), [summary]);
  const followThrough = useMemo(() => buildFollowThrough(summary), [summary]);
  const characterGlyphs = useMemo(() => buildCharacterGlyphs(summary, followThrough), [summary, followThrough]);
  const avatarGrowth = useMemo(() => buildAvatarGrowth(summary, followThrough), [summary, followThrough]);

  if (loading && !summary) return <LoadingCard label="Loading Evolution..." />;
  if (error && !summary) return <ErrorCard message={error} onRetry={onRefresh} />;

  return (
    <div className="space-y-4">
      <PageTitle eyebrow="Evolution" title="Your character is taking shape." body="Early form. Real signals. The avatar grows when signals become action." />

      <section className="relative overflow-hidden rounded-[2.1rem] border border-violet-300/20 bg-gradient-to-br from-violet-500/15 via-black/35 to-cyan-500/10 p-5 shadow-2xl shadow-violet-500/10">
        <div className="evolution-hero-glow" />
        <div className="relative z-10 grid gap-5">
          <AvatarStage character={character} followThrough={followThrough} glyphs={characterGlyphs} growth={avatarGrowth} />
          <div className="grid grid-cols-2 gap-3">
            <InfoTile label="State" value={character?.current_state || "Exploring"} />
            <InfoTile label="Identity" value={character?.identity_label || "Unknown"} />
            <InfoTile label="Signals" value={character?.accepted_signal_count ?? 0} />
            <InfoTile label="Forge" value={character?.forge_state || "Cold"} />
          </div>
        </div>
      </section>

      <AvatarGrowthPanel growth={avatarGrowth} />

      <CompactJotTrailSection summary={jotSummary} />

      <section className="rounded-[2rem] border border-cyan-300/18 bg-cyan-500/8 p-5 shadow-xl shadow-cyan-500/8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-200">Early Pattern Map</p>
            <h3 className="mt-2 text-2xl font-black">Not a label. A direction.</h3>
          </div>
          <span className="rounded-full border border-cyan-300/20 bg-cyan-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-cyan-100">Live</span>
        </div>
        <div className="mt-5">
          <PatternRadar axes={patternAxes} />
        </div>
        <p className="mt-4 text-sm leading-6 text-zinc-400">Built from your signals so far. The shape becomes less generic as the deck learns from you.</p>
      </section>

      <section className="rounded-[1.8rem] border border-orange-300/18 bg-orange-500/8 p-5">
        <p className="text-xs uppercase tracking-[0.24em] text-orange-200">Follow-through</p>
        <FollowThroughPanel followThrough={followThrough} character={character} />
      </section>

      <section className="rounded-[1.7rem] border border-white/10 bg-white/[0.045] p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-200/80">Unlocked cards</p>
            <h3 className="mt-1 text-lg font-black">Signal tools</h3>
          </div>
          <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1 text-xs text-zinc-300">{cardTypes.length}</span>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {cardTypes.length ? cardTypes.map((type) => <span key={type} className="rounded-full border border-cyan-300/20 bg-cyan-500/10 px-3 py-2 text-xs font-semibold text-cyan-100">{type}</span>) : <SmallEmptyState text="Interact with the Feed to unlock card types." />}
        </div>
      </section>

      <section className="rounded-[1.7rem] border border-amber-300/20 bg-amber-500/10 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-amber-200">Achievements</p>
            <h3 className="mt-1 text-base font-black">Growth marks</h3>
          </div>
          <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1 text-xs text-zinc-300">{unlockedCount}/{achievements.length}</span>
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2">
          {achievements.length ? achievements.map((achievement) => (
            <AchievementChip
              key={achievement.code || achievement.title}
              achievement={achievement}
              open={openAchievementCode === (achievement.code || achievement.title)}
              onToggle={() => setOpenAchievementCode((current) => current === (achievement.code || achievement.title) ? null : (achievement.code || achievement.title))}
            />
          )) : <SmallEmptyState text="Growth marks appear as the character acts." />}
        </div>
      </section>

      <CompactNextInsightSection nextUnlock={nextUnlock} insights={insights} />
    </div>
  );
}

function buildPatternAxes(summary) {
  const character = summary?.character || {};
  const accepted = Number(character.accepted_signal_count || 0);
  const total = Number(character.total_signal_count || accepted || 0);
  const forgeDays = Number(character.forge_days || 0);
  const alignment = Number(character.today_alignment || 0);
  const achievements = summary?.achievements || [];
  const insights = summary?.insights || [];
  const unlockedRatio = achievements.length ? achievements.filter((item) => item.unlocked).length / achievements.length : 0;
  const signalDepth = clamp01(accepted / 50);
  const signalBreadth = clamp01(total / 80);
  const forgeDepth = clamp01(forgeDays / 7);
  const alignmentDepth = clamp01(alignment / 100);
  const insightDepth = clamp01(insights.length / 3);
  const acceptanceRatio = total ? clamp01(accepted / total) : 0.35;

  return [
    { label: "Build", value: clamp01(0.26 + signalDepth * 0.34 + forgeDepth * 0.24 + unlockedRatio * 0.16) },
    { label: "Act", value: clamp01(0.22 + alignmentDepth * 0.38 + forgeDepth * 0.28 + unlockedRatio * 0.12) },
    { label: "Learn", value: clamp01(0.25 + signalDepth * 0.36 + insightDepth * 0.22 + unlockedRatio * 0.17) },
    { label: "Create", value: clamp01(0.2 + signalBreadth * 0.32 + insightDepth * 0.22 + signalDepth * 0.18) },
    { label: "Connect", value: clamp01(0.18 + acceptanceRatio * 0.26 + signalDepth * 0.26 + unlockedRatio * 0.18) },
    { label: "Reflect", value: clamp01(0.24 + insightDepth * 0.28 + signalDepth * 0.28 + acceptanceRatio * 0.16) },
  ];
}

function buildFollowThrough(summary) {
  const character = summary?.character || {};
  const alignment = clamp01(Number(character.today_alignment || 0) / 100);
  const forgeDays = Number(character.forge_days || 0);
  const forgeConsistency = clamp01(forgeDays / 14);
  const activeForgeState = character.forge_state && character.forge_state !== "Cold" && character.forge_state !== "Cooling";
  const completedActionProxy = activeForgeState ? Math.max(alignment, 0.45) : alignment * 0.55;
  const coolingPenalty = character.forge_cooling ? 0.08 : 0;
  const score = clamp01(forgeConsistency * 0.4 + alignment * 0.4 + completedActionProxy * 0.2 - coolingPenalty);

  let label = "Unformed";
  if (score >= 0.78) label = "Forged";
  else if (score >= 0.58) label = "Steady";
  else if (score >= 0.38) label = "Forming";
  else if (score >= 0.18) label = "Sparking";

  return {
    score,
    label,
    forgeDays,
    alignment: Math.round(alignment * 100),
    cooling: Boolean(character.forge_cooling),
  };
}

function buildCharacterGlyphs(summary, followThrough) {
  const character = summary?.character || {};
  const accepted = Number(character.accepted_signal_count || 0);
  const insights = summary?.insights?.length || 0;
  const achievements = summary?.achievements || [];
  const unlockedAchievements = achievements.filter((item) => item.unlocked).length;
  const glyphs = [
    { icon: "✦", label: accepted >= 1 ? "Signal spark" : "Dormant signal", active: accepted >= 1 },
    { icon: "◈", label: accepted >= 7 ? "Pattern seed" : "Pattern hidden", active: accepted >= 7 },
    { icon: "🔥", label: followThrough.forgeDays >= 1 ? "Forge ember" : "Forge cold", active: followThrough.forgeDays >= 1 },
    { icon: "⌁", label: insights >= 1 ? "Insight trace" : "Insight locked", active: insights >= 1 },
    { icon: "⚑", label: unlockedAchievements >= 4 ? "Growth mark" : "Growth mark", active: unlockedAchievements >= 4 },
  ];
  return glyphs;
}

function buildAvatarGrowth(summary, followThrough) {
  const character = summary?.character || {};
  const accepted = Number(character.accepted_signal_count || 0);
  const total = Number(character.total_signal_count || accepted || 0);
  const insights = summary?.insights?.length || 0;
  const achievements = summary?.achievements || [];
  const unlockedAchievements = achievements.filter((item) => item.unlocked).length;

  const milestones = [
    {
      code: "signal_spark",
      label: "Signal Spark",
      requirement: "1 saved signal",
      unlocked: total >= 1,
      effect: "The face line wakes up.",
    },
    {
      code: "pattern_seed",
      label: "Pattern Seed",
      requirement: "7 signals",
      unlocked: total >= 7,
      effect: "The Pattern Map and cyan aura become clearer.",
    },
    {
      code: "forge_ember",
      label: "Forge Ember",
      requirement: "1 Forge day",
      unlocked: followThrough.forgeDays >= 1,
      effect: "Orange ember light reaches the cloak.",
    },
    {
      code: "steady_form",
      label: "Steady Form",
      requirement: "Steady follow-through",
      unlocked: ["Steady", "Forged"].includes(followThrough.label),
      effect: "The ring stabilizes around the traveler.",
    },
    {
      code: "insight_trace",
      label: "Insight Trace",
      requirement: "1 Insight unlocked",
      unlocked: insights >= 1,
      effect: "A violet trace appears from reflected patterns.",
    },
    {
      code: "growth_mark",
      label: "Growth Mark",
      requirement: "4 achievements",
      unlocked: unlockedAchievements >= 4,
      effect: "A visible growth mark is carried by the avatar.",
    },
  ];

  const unlocked = milestones.filter((milestone) => milestone.unlocked);
  const next = milestones.find((milestone) => !milestone.unlocked) || null;
  const stage = unlocked.length <= 1 ? "Emerging" : unlocked.length <= 3 ? "Taking shape" : unlocked.length <= 5 ? "Marked path" : "Distinct form";

  return {
    stage,
    level: unlocked.length,
    total: milestones.length,
    progress: milestones.length ? Math.round((unlocked.length / milestones.length) * 100) : 0,
    next,
    milestones,
  };
}

function clamp01(value) {
  if (Number.isNaN(value)) return 0;
  return Math.max(0, Math.min(1, value));
}

function AvatarStage({ character, followThrough, glyphs, growth }) {
  const level = Number(growth?.level || 0);
  const followLabel = followThrough?.label || "Unformed";
  const cooling = Boolean(followThrough?.cooling);
  const visibleStage = growth?.stage || "Undiscovered";
  const identity = character?.identity_label || "Undiscovered";
  const faceOpacity = Math.min(0.95, 0.38 + level * 0.1);
  const auraOpacity = Math.min(0.52, 0.22 + level * 0.055);
  const emberOpacity = level >= 2 ? 0.95 : level >= 1 ? 0.5 : 0.2;
  const ringOpacity = ["Steady", "Forged"].includes(followLabel) ? 0.75 : followLabel === "Forming" ? 0.46 : 0.28;

  return (
    <div className="grid gap-4">
      <div className="relative mx-auto w-full max-w-[19rem] overflow-hidden rounded-[2.2rem] border border-cyan-300/20 bg-gradient-to-b from-zinc-950 via-violet-950/20 to-cyan-950/10 p-4 shadow-2xl shadow-cyan-500/10">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_24%,rgba(34,211,238,0.22),transparent_30%),radial-gradient(circle_at_50%_78%,rgba(168,85,247,0.2),transparent_42%)]" />
        <div className="relative">
          <svg className="mx-auto block h-[20rem] w-full max-w-[16.5rem]" viewBox="0 0 260 320" role="img" aria-label="Visible hooded traveler avatar">
            <defs>
              <radialGradient id="avatarAura31" cx="50%" cy="35%" r="66%">
                <stop offset="0%" stopColor="#67e8f9" stopOpacity="0.42" />
                <stop offset="48%" stopColor="#8b5cf6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#020617" stopOpacity="0" />
              </radialGradient>
              <linearGradient id="cloakGrad31" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0%" stopColor="#0f172a" />
                <stop offset="52%" stopColor="#050816" />
                <stop offset="100%" stopColor="#0e7490" stopOpacity="0.42" />
              </linearGradient>
              <linearGradient id="hoodGrad31" x1="0" x2="1" y1="0" y2="1">
                <stop offset="0%" stopColor="#1e293b" />
                <stop offset="54%" stopColor="#070914" />
                <stop offset="100%" stopColor="#312e81" stopOpacity="0.6" />
              </linearGradient>
              <filter id="softGlow31" x="-40%" y="-40%" width="180%" height="180%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            <circle cx="130" cy="152" r="116" fill="url(#avatarAura31)" opacity={auraOpacity} />
            <circle cx="130" cy="160" r="106" fill="none" stroke="#22d3ee" strokeOpacity={ringOpacity} strokeWidth="2" strokeDasharray={cooling ? "5 12" : "18 10"} />
            <circle cx="130" cy="160" r="82" fill="none" stroke="#a78bfa" strokeOpacity="0.22" strokeWidth="1" />

            {level >= 2 ? (
              <g opacity="0.62" stroke="#22d3ee" strokeWidth="1.4" strokeLinecap="round">
                <path d="M55 188 C86 176, 104 158, 130 132 C156 158, 174 176, 205 188" fill="none" />
                <path d="M76 222 C104 210, 118 196, 130 176 C142 196, 156 210, 184 222" fill="none" strokeOpacity="0.45" />
                <path d="M130 72 L130 112" strokeOpacity="0.5" />
              </g>
            ) : null}

            <path d="M48 285 C57 222, 75 168, 103 129 C115 112, 145 112, 157 129 C185 168, 203 222, 212 285 Z" fill="url(#cloakGrad31)" stroke="#22d3ee" strokeOpacity="0.24" strokeWidth="2" />
            <path d="M76 285 C86 226, 100 184, 119 151 C126 140, 134 140, 141 151 C160 184, 174 226, 184 285 Z" fill="#020617" opacity="0.72" />
            <path d="M64 282 C83 244, 98 220, 121 195" fill="none" stroke="#67e8f9" strokeOpacity="0.2" strokeWidth="2" strokeLinecap="round" />
            <path d="M196 282 C177 244, 162 220, 139 195" fill="none" stroke="#a78bfa" strokeOpacity="0.24" strokeWidth="2" strokeLinecap="round" />

            <path d="M76 147 C78 84, 101 50, 130 44 C159 50, 182 84, 184 147 C170 124, 153 111, 130 111 C107 111, 90 124, 76 147 Z" fill="url(#hoodGrad31)" stroke="#67e8f9" strokeOpacity="0.36" strokeWidth="2.2" />
            <path d="M97 134 C101 101, 114 82, 130 78 C146 82, 159 101, 163 134 C152 125, 142 121, 130 121 C118 121, 108 125, 97 134 Z" fill="#01040b" stroke="#0e7490" strokeOpacity="0.35" strokeWidth="1.4" />
            <path d="M112 132 C120 127, 140 127, 148 132" fill="none" stroke="#cffafe" strokeOpacity={faceOpacity} strokeWidth="3" strokeLinecap="round" filter="url(#softGlow31)" />
            <circle cx="130" cy="147" r="7" fill="#67e8f9" opacity={Math.max(0.26, faceOpacity - 0.18)} filter="url(#softGlow31)" />

            <path d="M130 158 L130 242" stroke="#67e8f9" strokeOpacity="0.36" strokeWidth="2" strokeLinecap="round" />
            <path d="M117 196 L143 196" stroke="#a78bfa" strokeOpacity="0.28" strokeWidth="1.5" strokeLinecap="round" />

            {level >= 1 ? (
              <g filter="url(#softGlow31)">
                <circle cx="130" cy="205" r="8" fill="#fb923c" opacity={emberOpacity} />
                <path d="M130 193 C122 205, 127 215, 130 220 C136 211, 138 202, 130 193 Z" fill="#fed7aa" opacity="0.72" />
              </g>
            ) : null}

            {level >= 4 ? (
              <g opacity="0.72" stroke="#c4b5fd" strokeWidth="2" strokeLinecap="round">
                <path d="M91 92 L70 72" />
                <path d="M169 92 L190 72" />
                <path d="M92 246 L72 264" />
                <path d="M168 246 L188 264" />
              </g>
            ) : null}

            {level >= 5 ? (
              <g transform="translate(171 177)" filter="url(#softGlow31)">
                <path d="M0 -13 L9 0 L0 13 L-9 0 Z" fill="#22d3ee" opacity="0.82" />
                <path d="M0 -6 L4 0 L0 6 L-4 0 Z" fill="#ecfeff" opacity="0.9" />
              </g>
            ) : null}

            <g className={cooling ? "opacity-45" : "opacity-85"}>
              <text x="130" y="306" textAnchor="middle" fill="#a5f3fc" fontSize="10" fontWeight="800" letterSpacing="3">
                {cooling ? "FORGE COOLING" : visibleStage.toUpperCase()}
              </text>
            </g>
          </svg>

          <div className="absolute left-4 top-4 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-cyan-100">
            Visible form
          </div>
          <div className="absolute bottom-4 right-4 rounded-full border border-violet-300/20 bg-black/45 px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-violet-100">
            {growth.level}/{growth.total} marks
          </div>
        </div>
      </div>

      <div className="text-center">
        <p className="text-[10px] uppercase tracking-[0.26em] text-violet-200/80">Character form</p>
        <h3 className="mt-1 text-2xl font-black">{identity}</h3>
        <p className="mt-2 text-sm text-zinc-400">
          Dark hooded traveler · {cooling ? "Forge cooling" : `${followLabel} follow-through`}
        </p>
        <p className="mx-auto mt-2 max-w-xs text-xs leading-5 text-zinc-500">
          The base form is always visible. New marks appear when signals become action.
        </p>
      </div>

      <div className="grid grid-cols-5 gap-2">
        {glyphs.map((glyph) => (
          <div key={`${glyph.icon}-${glyph.label}`} className={`rounded-2xl border px-2 py-3 text-center ${glyph.active ? "border-cyan-300/25 bg-cyan-400/10 text-cyan-100" : "border-white/10 bg-black/20 text-zinc-600"}`}>
            <span className="block text-lg leading-none">{glyph.icon}</span>
            <span className="mt-2 block truncate text-[9px] font-bold uppercase tracking-[0.1em]">{glyph.active ? "Lit" : "Locked"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AvatarGrowthPanel({ growth }) {
  return (
    <section className="rounded-[1.8rem] border border-violet-300/18 bg-violet-500/8 p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-violet-200/80">Avatar growth</p>
          <h3 className="mt-1 text-lg font-black">{growth.stage}</h3>
        </div>
        <span className="rounded-full border border-white/10 bg-black/25 px-3 py-1 text-xs font-bold text-zinc-300">{growth.level}/{growth.total}</span>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-violet-200 transition-all" style={{ width: `${growth.progress}%` }} />
      </div>
      <p className="mt-3 text-sm leading-6 text-zinc-400">
        {growth.next ? `Next visible change: ${growth.next.label} · ${growth.next.requirement}.` : "All current avatar growth marks are unlocked."}
      </p>
      <div className="mt-3 grid gap-2">
        {growth.milestones.map((milestone) => (
          <details key={milestone.code} className={`rounded-2xl border px-3 py-2 ${milestone.unlocked ? "border-violet-300/25 bg-violet-400/10" : "border-white/10 bg-black/20"}`}>
            <summary className="cursor-pointer list-none text-sm font-black text-white">
              <span className={milestone.unlocked ? "text-violet-100" : "text-zinc-500"}>{milestone.unlocked ? "✦" : "○"}</span> {milestone.label}
              <span className="ml-2 text-xs font-semibold text-zinc-500">{milestone.requirement}</span>
            </summary>
            <p className="mt-2 text-xs leading-5 text-zinc-400">{milestone.effect}</p>
          </details>
        ))}
      </div>
    </section>
  );
}


function CompactJotTrailSection({ summary }) {
  const [open, setOpen] = useState(false);
  const [openJotId, setOpenJotId] = useState(null);
  const total = summary?.total_jots ?? 0;
  const latest = summary?.latest_jots || [];
  const pathMessage = summary?.path_message || "No Jots yet. The deck is still mostly generic.";

  return (
    <section className="rounded-[1.65rem] border border-fuchsia-300/18 bg-fuchsia-500/8 p-4">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between gap-3 text-left active:scale-[0.99]">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-fuchsia-200/80">Jot Trail</p>
          <h3 className="mt-1 text-base font-black">Off the popular path</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-fuchsia-300/20 bg-fuchsia-500/10 px-3 py-1 text-xs font-bold text-fuchsia-100">{total} Jots</span>
          <span className="text-lg text-zinc-500">{open ? "⌃" : "›"}</span>
        </div>
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <p className="mt-3 text-sm leading-6 text-zinc-400">{pathMessage}</p>
            {latest.length ? (
              <div className="mt-3 grid gap-2">
                {latest.slice(0, 3).map((jot) => {
                  const jotOpen = openJotId === jot.id;
                  return (
                    <button
                      key={jot.id}
                      type="button"
                      onClick={() => setOpenJotId((current) => current === jot.id ? null : jot.id)}
                      className="rounded-2xl border border-white/10 bg-black/24 p-3 text-left transition active:scale-[0.98]"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="truncate text-xs font-bold uppercase tracking-[0.16em] text-zinc-500">{jot.prompt || "Micro-Jot"}</span>
                        <span className="text-[10px] font-bold text-fuchsia-100">{jotOpen ? "Hide" : "Reveal"}</span>
                      </div>
                      <AnimatePresence initial={false}>
                        {jotOpen ? (
                          <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mt-2 overflow-hidden text-sm leading-6 text-zinc-200">
                            “{jot.content}”
                          </motion.p>
                        ) : null}
                      </AnimatePresence>
                    </button>
                  );
                })}
              </div>
            ) : (
              <p className="mt-3 rounded-2xl border border-white/10 bg-black/20 p-3 text-sm leading-6 text-zinc-500">Rare Micro-Jots will appear in the Feed. They become the personalization layer.</p>
            )}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

function CompactNextInsightSection({ nextUnlock, insights }) {
  const [open, setOpen] = useState(false);
  const progress = nextUnlock?.progress_percent ?? 0;
  const remaining = nextUnlock?.signals_until_next_unlock ?? 50;

  return (
    <section className="rounded-[1.65rem] border border-emerald-300/20 bg-emerald-500/8 p-4">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between gap-3 text-left active:scale-[0.99]">
        <div>
          <p className="text-[10px] uppercase tracking-[0.24em] text-emerald-200">Next Insight</p>
          <h3 className="mt-1 text-base font-black">{remaining} signals away</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="rounded-full border border-emerald-300/20 bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-100">{progress}%</span>
          <span className="text-lg text-zinc-500">{open ? "⌃" : "›"}</span>
        </div>
      </button>
      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-emerald-200" style={{ width: `${progress}%` }} />
      </div>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="overflow-hidden">
            <p className="mt-3 text-sm leading-6 text-zinc-400">Insights reflect repeated patterns back to you after enough accepted signals.</p>
            {insights?.length ? (
              <div className="mt-3 grid gap-2">
                {insights.map((insight) => (
                  <article key={insight.id} className="rounded-2xl border border-white/10 bg-black/25 p-3">
                    <p className="font-black text-white">{insight.title}</p>
                    <p className="mt-1 text-sm leading-6 text-zinc-400">{insight.content}</p>
                  </article>
                ))}
              </div>
            ) : null}
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}

function PatternRadar({ axes }) {
  const size = 260;
  const center = size / 2;
  const maxRadius = 86;
  const points = axes.map((axis, index) => radarPoint(center, maxRadius * axis.value, index, axes.length));
  const polygonPoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const rings = [0.33, 0.66, 1];

  return (
    <div className="pattern-map-card">
      <svg viewBox={`0 0 ${size} ${size}`} className="mx-auto block h-[17rem] w-full max-w-[19rem]" role="img" aria-label="Early Pattern Map radar chart">
        <defs>
          <radialGradient id="patternGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(34, 211, 238, 0.34)" />
            <stop offset="100%" stopColor="rgba(139, 92, 246, 0.04)" />
          </radialGradient>
          <linearGradient id="patternStroke" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#67e8f9" />
            <stop offset="100%" stopColor="#c4b5fd" />
          </linearGradient>
        </defs>
        {rings.map((ring) => (
          <polygon
            key={ring}
            points={axes.map((_, index) => {
              const point = radarPoint(center, maxRadius * ring, index, axes.length);
              return `${point.x},${point.y}`;
            }).join(" ")}
            fill="none"
            stroke="rgba(255,255,255,0.12)"
            strokeWidth="1"
          />
        ))}
        {axes.map((axis, index) => {
          const outer = radarPoint(center, maxRadius, index, axes.length);
          const label = radarPoint(center, maxRadius + 31, index, axes.length);
          return (
            <g key={axis.label}>
              <line x1={center} y1={center} x2={outer.x} y2={outer.y} stroke="rgba(255,255,255,0.10)" strokeWidth="1" />
              <text x={label.x} y={label.y} textAnchor="middle" dominantBaseline="middle" className="pattern-axis-label">{axis.label}</text>
            </g>
          );
        })}
        <polygon points={polygonPoints} fill="url(#patternGlow)" stroke="url(#patternStroke)" strokeWidth="3" strokeLinejoin="round" />
        {points.map((point, index) => <circle key={axes[index].label} cx={point.x} cy={point.y} r="4" fill="#cffafe" className="pattern-node" />)}
        <circle cx={center} cy={center} r="4" fill="rgba(255,255,255,0.55)" />
      </svg>
    </div>
  );
}

function radarPoint(center, radius, index, total) {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / total;
  return {
    x: center + Math.cos(angle) * radius,
    y: center + Math.sin(angle) * radius,
  };
}

function FollowThroughPanel({ followThrough, character }) {
  const ringDegrees = Math.round(followThrough.score * 360);
  return (
    <div className="mt-4 flex items-center gap-4">
      <div className="follow-ring" style={{ "--follow-angle": `${ringDegrees}deg` }}>
        <div className="follow-ring-inner">
          <span>{followThrough.label}</span>
        </div>
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="text-2xl font-black leading-tight">Follow-through: {followThrough.label}</h3>
        <p className="mt-2 text-sm leading-6 text-zinc-400">Separate from the Pattern Map. This tracks how often intention becomes action.</p>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <InfoTile label="Alignment" value={`${followThrough.alignment}%`} />
          <InfoTile label="Forge days" value={followThrough.forgeDays || character?.forge_days || 0} />
        </div>
      </div>
    </div>
  );
}

function AchievementChip({ achievement, open, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={`min-h-[3.75rem] rounded-2xl border p-2.5 text-left transition active:scale-[0.98] ${achievement.unlocked ? "border-amber-300/25 bg-amber-400/10" : "border-white/10 bg-black/20 opacity-65"}`}
    >
      <div className="flex items-start gap-2">
        <span className="text-base leading-none">{achievement.icon}</span>
        <div className="min-w-0 flex-1">
          <p className="line-clamp-2 text-[12px] font-black leading-[0.95rem] text-white">{achievement.title}</p>
          <p className={`mt-1 text-[9px] font-bold uppercase tracking-[0.12em] ${achievement.unlocked ? "text-amber-100" : "text-zinc-500"}`}>{achievement.unlocked ? "Unlocked" : "Locked"}</p>
        </div>
      </div>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.p
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 overflow-hidden text-xs leading-5 text-zinc-400"
          >
            {achievement.description}
          </motion.p>
        ) : null}
      </AnimatePresence>
    </button>
  );
}


function DevToolsPage({ status, loading, error, smoke, smokeLoading, smokeError, isDev, onRefresh, onRunSmoke, onBack }) {
  const counts = status?.counts || {};
  const systems = status?.systems || {};
  const notes = status?.dev_notes || [];
  const smokeSummary = smoke?.summary || null;
  const smokeChecks = smoke?.checks || [];
  const [qaState, setQaState] = useState(() => getStoredQaState());

  const completedQa = STEP26_QA_ITEMS.filter((item) => qaState[item.id]).length;
  const qaPercent = Math.round((completedQa / STEP26_QA_ITEMS.length) * 100);

  function toggleQaItem(itemId) {
    setQaState((current) => {
      const next = { ...current, [itemId]: !current[itemId] };
      localStorage.setItem(STEP26_QA_KEY, JSON.stringify(next));
      return next;
    });
  }

  function resetQaChecklist() {
    const cleared = STEP26_QA_ITEMS.reduce((acc, item) => {
      acc[item.id] = false;
      return acc;
    }, {});
    localStorage.setItem(STEP26_QA_KEY, JSON.stringify(cleared));
    setQaState(cleared);
  }

  if (!isDev) {
    return (
      <div className="flex flex-1 flex-col gap-4">
        <PageTitle eyebrow="Protected" title="Dev tools are hidden." body="Normal users stay inside the product experience." />
        <button onClick={onBack} className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 font-black text-white active:scale-[0.98]">
          Back to Evolution
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      <section className="rounded-[2rem] border border-cyan-300/20 bg-cyan-500/10 p-5 shadow-xl shadow-cyan-500/10">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.26em] text-cyan-200/80">Step 26 · Dev QA</p>
            <h2 className="mt-3 text-3xl font-black leading-tight tracking-tight">MVP confidence pass.</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-300">Run the smoke check, then mark the manual flow. This stays separate from the normal product UI.</p>
          </div>
          <button onClick={onBack} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-xs font-black text-zinc-300 active:scale-95">
            Close
          </button>
        </div>
      </section>

      <div className="grid grid-cols-2 gap-3">
        <InfoTile label="API" value={status?.status || (loading ? "loading" : "—")} />
        <InfoTile label="Version" value={status?.app_version || smoke?.app_version || "—"} />
        <InfoTile label="Smoke" value={smoke?.status || (smokeLoading ? "running" : "—")} />
        <InfoTile label="QA" value={`${completedQa}/${STEP26_QA_ITEMS.length}`} />
      </div>

      {error ? <Notice tone="error">{error}</Notice> : null}
      {smokeError ? <Notice tone="error">{smokeError}</Notice> : null}

      <div className="grid grid-cols-2 gap-3">
        <button onClick={onRefresh} disabled={loading} className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 font-black text-white active:scale-[0.98] disabled:opacity-60">
          {loading ? "Refreshing..." : "Refresh status"}
        </button>
        <button onClick={onRunSmoke} disabled={smokeLoading} className="rounded-2xl bg-white px-4 py-4 font-black text-zinc-950 active:scale-[0.98] disabled:opacity-60">
          {smokeLoading ? "Running..." : "Run smoke check"}
        </button>
      </div>

      <section className="rounded-[1.7rem] border border-emerald-300/20 bg-emerald-500/10 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-emerald-100/80">MVP smoke check</p>
            <h3 className="mt-2 text-xl font-black">{smoke?.status === "pass" ? "Core systems pass." : smokeLoading ? "Checking systems..." : "Run before demo."}</h3>
          </div>
          {smokeSummary ? <span className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-xs font-black text-emerald-100">{smokeSummary.passed}/{smokeSummary.checks}</span> : null}
        </div>

        {smokeSummary ? (
          <div className="mt-4 grid grid-cols-3 gap-2">
            <InfoTile label="Pass" value={smokeSummary.passed} />
            <InfoTile label="Warn" value={smokeSummary.warnings} />
            <InfoTile label="Fail" value={smokeSummary.failures} />
          </div>
        ) : null}

        <div className="mt-4 grid gap-2">
          {smokeChecks.map((check) => (
            <SmokeCheckRow key={check.key} check={check} />
          ))}
        </div>
        {smokeChecks.length === 0 && !smokeLoading ? <SmallEmptyState text="No smoke check run yet." /> : null}
      </section>

      <section className="rounded-[1.7rem] border border-violet-300/20 bg-violet-500/10 p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-violet-100/80">Manual QA checklist</p>
            <h3 className="mt-2 text-xl font-black">{qaPercent}% checked.</h3>
            <p className="mt-2 text-sm leading-6 text-zinc-300">Tap each row only after testing it on the phone-sized UI.</p>
          </div>
          <button onClick={resetQaChecklist} className="rounded-full border border-white/10 bg-black/20 px-3 py-2 text-xs font-black text-zinc-300 active:scale-95">
            Reset
          </button>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-black/30">
          <div className="h-full rounded-full bg-violet-200 transition-all" style={{ width: `${qaPercent}%` }} />
        </div>
        <div className="mt-4 grid gap-2">
          {STEP26_QA_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => toggleQaItem(item.id)}
              className={`rounded-2xl border px-3 py-3 text-left transition active:scale-[0.98] ${qaState[item.id] ? "border-emerald-300/25 bg-emerald-400/10" : "border-white/10 bg-black/20"}`}
            >
              <div className="flex items-start gap-3">
                <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full border text-xs font-black ${qaState[item.id] ? "border-emerald-200/30 bg-emerald-300 text-zinc-950" : "border-white/10 bg-white/[0.04] text-zinc-500"}`}>
                  {qaState[item.id] ? "✓" : ""}
                </span>
                <div>
                  <p className="text-sm font-black text-white">{item.title}</p>
                  <p className="mt-1 text-xs leading-5 text-zinc-400">{item.hint}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="rounded-[1.7rem] border border-white/10 bg-white/[0.045] p-4">
        <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">Database counts</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          {Object.entries(counts).map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-white/10 bg-black/20 p-3">
              <p className="text-[9px] uppercase tracking-[0.16em] text-zinc-500">{key.replaceAll("_", " ")}</p>
              <p className="mt-1 text-lg font-black text-white">{value}</p>
            </div>
          ))}
        </div>
        {Object.keys(counts).length === 0 && !loading ? <SmallEmptyState text="No dev status loaded yet." /> : null}
      </section>

      <section className="rounded-[1.7rem] border border-white/10 bg-black/25 p-4">
        <p className="text-[10px] uppercase tracking-[0.24em] text-zinc-500">Systems</p>
        <div className="mt-3 grid gap-2">
          {Object.entries(systems).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.04] px-3 py-3 text-sm">
              <span className="capitalize text-zinc-400">{key.replaceAll("_", " ")}</span>
              <span className="font-black text-cyan-100">{value}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[1.7rem] border border-amber-300/20 bg-amber-500/10 p-4">
        <p className="text-[10px] uppercase tracking-[0.24em] text-amber-100/80">Dev notes</p>
        <div className="mt-3 grid gap-2">
          {notes.map((note) => (
            <p key={note} className="rounded-2xl border border-amber-200/10 bg-black/20 px-3 py-3 text-sm leading-6 text-zinc-300">{note}</p>
          ))}
        </div>
      </section>
    </div>
  );
}

function SmokeCheckRow({ check }) {
  const statusClass = {
    pass: "border-emerald-300/25 bg-emerald-400/10 text-emerald-100",
    warn: "border-amber-300/25 bg-amber-400/10 text-amber-100",
    fail: "border-red-300/25 bg-red-400/10 text-red-100",
  };
  const symbol = check.status === "pass" ? "✓" : check.status === "warn" ? "!" : "×";

  return (
    <div className={`rounded-2xl border px-3 py-3 ${statusClass[check.status] || statusClass.warn}`}>
      <div className="flex items-start gap-3">
        <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-black/25 text-xs font-black">{symbol}</span>
        <div>
          <p className="text-sm font-black text-white">{check.label}</p>
          <p className="mt-1 text-xs leading-5 text-zinc-300">{check.detail}</p>
        </div>
      </div>
    </div>
  );
}

function PageTitle({ eyebrow, title, body }) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-5 shadow-xl shadow-black/20">
      <p className="text-xs uppercase tracking-[0.26em] text-zinc-500">{eyebrow}</p>
      <h2 className="mt-3 text-3xl font-black leading-tight tracking-tight">{title}</h2>
      {body ? <p className="mt-3 text-sm leading-6 text-zinc-400">{body}</p> : null}
    </section>
  );
}

function OnboardingGate({ acceptedSignals, totalSignals, onRestart, onCreateAccount, onSignIn }) {
  return (
    <section className="my-auto rounded-[2rem] border border-emerald-300/20 bg-gradient-to-br from-emerald-500/15 via-zinc-950 to-cyan-500/10 p-6 shadow-2xl shadow-emerald-500/10">
      <p className="text-xs uppercase tracking-[0.28em] text-emerald-200">Gate opened</p>
      <h2 className="mt-4 text-3xl font-black leading-tight">Your first signals are captured.</h2>
      <p className="mt-4 text-sm leading-6 text-zinc-300">Create an account to let the backend remember them.</p>
      <div className="mt-6 grid grid-cols-2 gap-3">
        <InfoTile label="Signals" value={totalSignals} />
        <InfoTile label="Accepted" value={acceptedSignals} />
      </div>
      <div className="mt-6 grid gap-3">
        <button onClick={onCreateAccount} className="rounded-2xl bg-white px-4 py-4 font-black text-zinc-950 active:scale-[0.98]">Create account</button>
        <button onClick={onSignIn} className="rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 font-bold text-white active:scale-[0.98]">Already have an account? Sign in</button>
        <button onClick={onRestart} className="rounded-2xl px-4 py-3 text-sm font-semibold text-zinc-400">Restart demo</button>
      </div>
    </section>
  );
}

function AuthModal({ mode, onClose, onSwitchMode, onSubmit, loading, error }) {
  const [email, setEmail] = useState("ale@example.com");
  const [password, setPassword] = useState("password123");
  const [username, setUsername] = useState("ale");
  const [displayName, setDisplayName] = useState("Ale");
  const isRegister = mode === "register";

  function submit(event) {
    event.preventDefault();
    onSubmit({ email, password, username, displayName });
  }

  return (
    <motion.div className="fixed inset-0 z-50 grid place-items-end bg-black/70 p-4 backdrop-blur-sm sm:place-items-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.form onSubmit={submit} initial={{ y: 32, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 32, opacity: 0 }} className="w-full max-w-md rounded-[2rem] border border-white/10 bg-zinc-950 p-5 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-zinc-500">{isRegister ? "Create account" : "Sign in"}</p>
            <h2 className="mt-2 text-2xl font-black">{isRegister ? "Save your signals." : "Return to your path."}</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-2 text-sm text-zinc-300">Close</button>
        </div>
        <div className="mt-5 grid gap-3">
          <Input label="Email" value={email} onChange={setEmail} type="email" />
          <Input label="Password" value={password} onChange={setPassword} type="password" />
          {isRegister ? (
            <>
              <Input label="Username" value={username} onChange={setUsername} />
              <Input label="Display name" value={displayName} onChange={setDisplayName} />
            </>
          ) : null}
        </div>
        {error ? <Notice tone="error">{error}</Notice> : null}
        <button type="submit" disabled={loading} className="mt-5 w-full rounded-2xl bg-white px-4 py-4 font-black text-zinc-950 active:scale-[0.98] disabled:opacity-60">{loading ? "Working..." : isRegister ? "Create account" : "Sign in"}</button>
        <button type="button" onClick={onSwitchMode} className="mt-3 w-full rounded-2xl px-4 py-3 text-sm font-semibold text-zinc-400">{isRegister ? "Already have an account? Sign in" : "Need an account? Create one"}</button>
      </motion.form>
    </motion.div>
  );
}

function Input({ label, value, onChange, type = "text" }) {
  return (
    <label className="block">
      <span className="text-xs uppercase tracking-[0.18em] text-zinc-500">{label}</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} type={type} className="mt-2 w-full rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-4 text-base text-white outline-none placeholder:text-zinc-600 focus:border-cyan-200/40" />
    </label>
  );
}

function InfoTile({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/24 p-4">
      <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500">{label}</p>
      <p className="mt-2 truncate text-lg font-black text-white">{value}</p>
    </div>
  );
}

function Notice({ tone = "info", children }) {
  const classes = {
    info: "border-cyan-300/20 bg-cyan-500/10 text-cyan-100",
    success: "border-emerald-300/20 bg-emerald-500/10 text-emerald-100",
    error: "border-red-300/20 bg-red-500/10 text-red-100",
  };
  return <div className={`mt-4 rounded-2xl border px-4 py-3 text-sm font-semibold ${classes[tone] || classes.info}`}>{children}</div>;
}

function SmallEmptyState({ text }) {
  return <p className="mt-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-sm leading-6 text-zinc-400">{text}</p>;
}

function LoadingCard({ label = "Loading..." }) {
  return (
    <section className="my-auto rounded-[2rem] border border-white/10 bg-white/[0.045] p-6">
      <p className="text-sm text-zinc-400">{label}</p>
    </section>
  );
}

function ErrorCard({ message, onRetry }) {
  return (
    <section className="my-auto rounded-[2rem] border border-red-300/20 bg-red-500/10 p-6">
      <p className="text-sm leading-6 text-red-100">{message}</p>
      {onRetry ? <button onClick={onRetry} className="mt-4 rounded-2xl bg-white px-4 py-3 font-black text-zinc-950">Retry</button> : null}
    </section>
  );
}

function formatCardType(type) {
  if (!type) return "Card";
  return type.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function difficultyClass(difficulty) {
  if (difficulty === "Easy") return "border-emerald-300/20 bg-emerald-500/10 text-emerald-100";
  if (difficulty === "Medium") return "border-amber-300/20 bg-amber-500/10 text-amber-100";
  if (difficulty === "Hard") return "border-red-300/20 bg-red-500/10 text-red-100";
  return "border-white/10 bg-white/[0.06] text-zinc-200";
}
