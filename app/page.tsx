'use client';

import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import confetti from 'canvas-confetti';
import {
  Flame,
  Trophy,
  Plus,
  Trash2,
  Check,
  Calendar,
  Sparkles,
  Award,
  Zap,
  Sword,
  X,
  ShoppingBag,
  User,
  Crown,
  Gift,
  CheckCircle2,
  LogOut,
  ChevronRight,
  ChevronLeft,
  Mail,
  Lock,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  RotateCw,
  Medal,
  Bell,
  Settings,
  Volume2,
  VolumeX,
  BellOff,
  ExternalLink,
  FileText,
  Pencil
} from 'lucide-react';
import {
  playQuestCompleteSound,
  playCoinSound,
  playLevelUpSound
} from './utils/audio';
import { initNativeApp, triggerHaptic, scheduleStreakProtectionReminder, isNativePlatform } from './utils/native';
import {
  PRIVACY_POLICY_URL,
  TERMS_OF_SERVICE_URL,
  SUPPORT_EMAIL,
  FEEDBACK_URL,
  APP_VERSION,
  BUILD_NUMBER
} from './constants/links';
import {
  auth,
  db,
  googleProvider,
  isFirebaseConfigured,
  UserProfile,
  HabitDocument,
  DIFFICULTY_REWARDS,
  MAX_FREE_HABITS,
  calculateLevel,
  getTodayKey,
  getYesterdayKey
} from './utils/firebase';
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithCredential,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  deleteUser,
  User as FirebaseUser
} from 'firebase/auth';
import { FirebaseAuthentication } from '@capacitor-firebase/authentication';
import {
  doc,
  getDoc,
  setDoc,
  updateDoc,
  deleteDoc,
  collection,
  query,
  where,
  orderBy,
  limit,
  getDocs,
  onSnapshot,
  increment,
  arrayUnion,
  arrayRemove,
  addDoc
} from 'firebase/firestore';

// --- Type Definitions ---
type Difficulty = 'easy' | 'medium' | 'hard';
type MainTab = 'quests' | 'leaderboard' | 'shop' | 'profile';
type AppScreen = 'loading' | 'auth' | 'character_setup' | 'main';
type LeaderboardTab = 'all_time' | 'streaks';

interface Habit {
  id: string;
  name: string;
  icon: string;
  difficulty: Difficulty;
  xpReward: number;
  goldReward: number;
  completedDates: string[];
  createdAt?: string;
}

interface PlayerStats {
  id: string;
  name: string;
  avatar: string;
  classTitle: string;
  level: number;
  currentXP: number;
  totalXP: number;
  gold: number;
  streakDays: number;
  lastCompletedDate: string | null;
  isPro: boolean;
  interestedInPro: boolean;
  unlockedBadgeIds: string[];
}

interface RewardItem {
  id: string;
  name: string;
  icon: string;
  cost: number;
  claimedCount: number;
  category: 'perk' | 'treat' | 'custom';
}

interface FloatingParticle {
  id: number;
  text: string;
  x: number;
  y: number;
  color: string;
}

interface Badge {
  id: string;
  name: string;
  description: string;
  icon: string;
  reqText: string;
}

const DIFFICULTY_MAP: Record<Difficulty, { label: string; xp: number; gold: number }> = {
  easy: { label: 'Easy', xp: 15, gold: 5 },
  medium: { label: 'Medium', xp: 30, gold: 10 },
  hard: { label: 'Hard', xp: 50, gold: 20 }
};

// 6 Starting RPG Classes
const AVATAR_OPTIONS = [
  { icon: '⚔️', title: 'Warrior', role: 'Shadow Blade', desc: 'Discipline & Physical Strength' },
  { icon: '🧙‍♂️', title: 'Mage', role: 'Arcane Sage', desc: 'Wisdom & Deep Knowledge' },
  { icon: '🛡️', title: 'Guardian', role: 'Iron Paladin', desc: 'Unwavering Daily Consistency' },
  { icon: '🥷', title: 'Ninja', role: 'Cyber Rogue', desc: 'Speed & Laser Focus' },
  { icon: '🧘', title: 'Monk', role: 'Zen Master', desc: 'Calm Mind & Spiritual Flow' },
  { icon: '🏹', title: 'Archer', role: 'Star Hunter', desc: 'Precision Goals & Targets' }
];

const EMOJI_BANK = ['⚡', '💧', '🏃', '📚', '🧘', '🥗', '💻', '💤', '✍️', '🏋️', '🎯', '🥑', '🔥', '🛡️', '🧠', '☕'];

const BADGES_LIST: Badge[] = [
  { id: 'first_blood', name: 'First Blood', description: 'Complete your first habit quest', icon: '🩸', reqText: '1 quest completed' },
  { id: 'streak_7', name: 'Unbroken Flame', description: 'Maintain a 7-day streak on any habit', icon: '🔥', reqText: '7-day streak' },
  { id: 'guild_hero', name: 'Guild Champion', description: 'Reach Level 5 and lead your squad', icon: '🛡️', reqText: 'Reach Level 5' },
  { id: 'gold_hoarder', name: 'Dragon Treasury', description: 'Accumulate over 300 Gold in your vault', icon: '💰', reqText: '300 Gold saved' },
  { id: 'century_slayer', name: 'Century Vanguard', description: 'Complete 25 total quests across your journey', icon: '⚡', reqText: '25 quests done' }
];

// 1-Tap Student Starter Quests (Play Store empty state)
const STARTER_QUESTS: { name: string; icon: string; difficulty: Difficulty; xpReward: number; goldReward: number }[] = [
  { name: '2 Hours Study / Coding', icon: '📚', difficulty: 'hard', xpReward: 50, goldReward: 20 },
  { name: '45m Gym / Workout', icon: '💪', difficulty: 'medium', xpReward: 30, goldReward: 10 },
  { name: 'Drink 3L Water', icon: '💧', difficulty: 'easy', xpReward: 15, goldReward: 5 },
  { name: 'Wake Up Before 7 AM', icon: '🌅', difficulty: 'medium', xpReward: 30, goldReward: 10 }
];

// Date helpers
const formatDateKey = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const addDays = (date: Date, days: number): Date => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

const getStartOfWeek = (date: Date): Date => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1);
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
};

const xpForLevel = (lvl: number): number => lvl * 120 + 80;

const getPlayerTitle = (lvl: number, baseRole = 'Hunter'): string => {
  if (lvl >= 25) return `Mythic ${baseRole}`;
  if (lvl >= 20) return `Grandmaster ${baseRole}`;
  if (lvl >= 15) return `Vanguard ${baseRole}`;
  if (lvl >= 10) return `Arcane ${baseRole}`;
  if (lvl >= 6) return `Elite ${baseRole}`;
  if (lvl >= 3) return `Adept ${baseRole}`;
  return `Novice ${baseRole}`;
};

const DEFAULT_REWARDS: RewardItem[] = [
  { id: 'r-1', name: '1 Hour Guilt-Free Gaming', icon: '🎮', cost: 100, claimedCount: 0, category: 'perk' },
  { id: 'r-2', name: 'Cheat Snack / Specialty Coffee', icon: '☕', cost: 80, claimedCount: 0, category: 'treat' },
  { id: 'r-3', name: 'Movie / Anime Binge Night', icon: '🎬', cost: 200, claimedCount: 0, category: 'perk' },
  { id: 'r-4', name: '30m Restful Power Nap', icon: '😴', cost: 60, claimedCount: 0, category: 'treat' }
];

export default function LevelUpApp() {
  const [isClient, setIsClient] = useState(false);
  const [currentScreen, setCurrentScreen] = useState<AppScreen>('loading');
  const [activeTab, setActiveTab] = useState<MainTab>('quests');

  // Auth & Session State
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [isSignUpMode, setIsSignUpMode] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [currentUser, setCurrentUser] = useState<FirebaseUser | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);

  // Character Creation State
  const [hunterName, setHunterName] = useState('');
  const [selectedAvatarIdx, setSelectedAvatarIdx] = useState(0);
  const [setupError, setSetupError] = useState<string | null>(null);
  const [setupLoading, setSetupLoading] = useState(false);

  // Quota-Safe Leaderboard State (5-minute cache to protect Firestore Spark limits)
  const LEADERBOARD_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
  const [leaderboardTab, setLeaderboardTab] = useState<LeaderboardTab>('all_time');
  const [leaderboardData, setLeaderboardData] = useState<UserProfile[]>([]);
  const [leaderboardLoading, setLeaderboardLoading] = useState(false);
  const [userRank, setUserRank] = useState<number | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<number>(Date.now());
  const leaderboardCacheRef = useRef<{
    all_time?: { data: UserProfile[]; timestamp: number };
    streaks?: { data: UserProfile[]; timestamp: number };
  }>({});

  // Player Profile State (Populated strictly from Firestore users/{uid})
  const [player, setPlayer] = useState<PlayerStats>({
    id: 'user_init',
    name: '',
    avatar: '⚔️',
    classTitle: 'Novice Hunter',
    level: 1,
    currentXP: 0,
    totalXP: 0,
    gold: 0,
    streakDays: 0,
    lastCompletedDate: null,
    isPro: false,
    interestedInPro: false,
    unlockedBadgeIds: ['first_blood']
  });

  const [habits, setHabits] = useState<Habit[]>([]);
  const [rewards, setRewards] = useState<RewardItem[]>(DEFAULT_REWARDS);
  const [weekOffset, setWeekOffset] = useState(0);

  // Modals & Notifications
  const [isAddQuestModal, setIsAddQuestModal] = useState(false);
  const [editingHabit, setEditingHabit] = useState<Habit | null>(null);
  const [editQuestName, setEditQuestName] = useState('');
  const [editQuestIcon, setEditQuestIcon] = useState('⚔️');
  const [editQuestDifficulty, setEditQuestDifficulty] = useState<Difficulty>('medium');
  const [isLevelUpModal, setIsLevelUpModal] = useState(false);
  const [levelUpData, setLevelUpData] = useState<{ newLevel: number; oldLevel: number; title: string } | null>(null);
  const [isAddRewardModal, setIsAddRewardModal] = useState(false);
  const [isSettingsModal, setIsSettingsModal] = useState(false);
  const [isDeleteAccountModal, setIsDeleteAccountModal] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Particles
  const [particles, setParticles] = useState<FloatingParticle[]>([]);
  const particleIdRef = useRef(0);

  // New Quest Form
  const [newQuestName, setNewQuestName] = useState('');
  const [newQuestIcon, setNewQuestIcon] = useState('⚡');
  const [newQuestDifficulty, setNewQuestDifficulty] = useState<Difficulty>('medium');

  // New Custom Reward Form
  const [newRewardName, setNewRewardName] = useState('');
  const [newRewardIcon, setNewRewardIcon] = useState('🎁');
  const [newRewardCost, setNewRewardCost] = useState(100);

  // Dates & Streaks
  const todayKey = useMemo(() => getTodayKey(), []);
  const yesterdayKey = useMemo(() => getYesterdayKey(), []);

  const weekDays = useMemo(() => {
    const baseDate = addDays(new Date(), weekOffset * 7);
    const startOfWeek = getStartOfWeek(baseDate);

    return Array.from({ length: 7 }, (_, i) => {
      const date = addDays(startOfWeek, i);
      const dateKey = formatDateKey(date);
      const isToday = dateKey === todayKey;
      const dayShort = date.toLocaleDateString('en-US', { weekday: 'narrow' });
      const dayNumber = date.getDate();
      const monthShort = date.toLocaleDateString('en-US', { month: 'short' });

      return { date, dateKey, isToday, dayShort, dayNumber, monthShort };
    });
  }, [weekOffset, todayKey]);

  const totalCompletedCount = useMemo(() => {
    return habits.reduce((acc, h) => acc + h.completedDates.length, 0);
  }, [habits]);

  const xpNeeded = useMemo(() => xpForLevel(player.level), [player.level]);
  const xpPercentage = useMemo(() => {
    return Math.min(100, Math.round((player.currentXP / xpNeeded) * 100));
  }, [player.currentXP, xpNeeded]);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage((current) => (current === msg ? null : current));
    }, 2500);
  };

  const spawnParticle = (text: string, color = '#F5B041', x?: number, y?: number) => {
    const id = ++particleIdRef.current;
    const posX = x || (typeof window !== 'undefined' ? window.innerWidth / 2 : 200);
    const posY = y || (typeof window !== 'undefined' ? window.innerHeight / 2 : 300);

    setParticles((prev) => [...prev, { id, text, x: posX, y: posY, color }]);
    setTimeout(() => {
      setParticles((prev) => prev.filter((p) => p.id !== id));
    }, 1100);
  };

  // ----------------------------------------------------
  // Verify User Profile in Firestore
  // ----------------------------------------------------
  const verifyUserProfile = useCallback(async (userId: string) => {
    try {
      const userDocRef = doc(db, 'users', userId);
      const userSnap = await getDoc(userDocRef);

      if (userSnap.exists()) {
        const data = userSnap.data() as UserProfile;
        if (data.username && data.username.trim().length >= 3) {
          const classOption = AVATAR_OPTIONS.find((a) => a.icon === data.avatar_id) || AVATAR_OPTIONS[0];
          const loadedPlayer: PlayerStats = {
            id: userId,
            name: data.username,
            avatar: data.avatar_id || '⚔️',
            classTitle: getPlayerTitle(data.level || 1, classOption.title),
            level: data.level || 1,
            currentXP: data.xp || 0,
            totalXP: data.total_xp || 0,
            gold: data.gold || 0,
            streakDays: data.streak_days || 0,
            lastCompletedDate: data.last_completed_date || null,
            isPro: !!data.is_pro,
            interestedInPro: !!data.interested_in_pro,
            unlockedBadgeIds: ['first_blood']
          };

          setPlayer(loadedPlayer);
          localStorage.setItem('levelup_player', JSON.stringify(loadedPlayer));
          setCurrentScreen('main');
          return;
        }
      }
      // If document missing or username empty, route to character creation
      setCurrentScreen('character_setup');
    } catch (err) {
      console.warn('Profile verification exception:', err);
      // Check local cache for offline resiliency
      const cachedPlayer = localStorage.getItem('levelup_player');
      if (cachedPlayer) {
        try {
          const parsed = JSON.parse(cachedPlayer);
          if (parsed.name) {
            setPlayer(parsed);
            setCurrentScreen('main');
            return;
          }
        } catch {}
      }
      setCurrentScreen('character_setup');
    }
  }, []);

  // ----------------------------------------------------
  // Real-time Habit (Quest) Sync via Firestore Subcollection
  // users/{uid}/habits/{habitId}
  // ----------------------------------------------------
  useEffect(() => {
    if (!currentUserId || currentScreen !== 'main') return;

    try {
      const habitsCol = collection(db, 'users', currentUserId, 'habits');
      const q = query(habitsCol, orderBy('created_at', 'desc'));

      const unsubscribe = onSnapshot(
        q,
        (snapshot) => {
          const loadedHabits: Habit[] = snapshot.docs.map((docSnap) => {
            const data = docSnap.data() as HabitDocument;
            const diffKey = (data.difficulty || 'medium') as Difficulty;
            const reward = DIFFICULTY_REWARDS[diffKey] || DIFFICULTY_REWARDS.medium;
            return {
              id: docSnap.id,
              name: data.title,
              icon: data.icon || '⚡',
              difficulty: diffKey,
              xpReward: reward.xp,
              goldReward: reward.gold,
              completedDates: Array.isArray(data.completed_dates) ? data.completed_dates : [],
              createdAt: data.created_at
            };
          });
          setHabits(loadedHabits);
          localStorage.setItem('levelup_habits', JSON.stringify(loadedHabits));
        },
        (error) => {
          console.warn('Habits snapshot error:', error);
          const cached = localStorage.getItem('levelup_habits');
          if (cached) {
            try {
              setHabits(JSON.parse(cached));
            } catch {}
          }
        }
      );

      return () => unsubscribe();
    } catch (e) {
      console.warn('Habits subscription failed:', e);
    }
  }, [currentUserId, currentScreen]);

  // ----------------------------------------------------
  // Real-time Player Document Listener
  // ----------------------------------------------------
  useEffect(() => {
    if (!currentUserId || currentScreen !== 'main') return;

    try {
      const userDocRef = doc(db, 'users', currentUserId);
      const unsubscribe = onSnapshot(
        userDocRef,
        (docSnap) => {
          if (!docSnap.exists()) return;
          const data = docSnap.data() as UserProfile;
          setPlayer((prev) => {
            const calculatedLvl = calculateLevel(data.total_xp || 0);
            const classOption = AVATAR_OPTIONS.find((a) => a.icon === data.avatar_id) || AVATAR_OPTIONS[0];
            return {
              ...prev,
              name: data.username || prev.name,
              avatar: data.avatar_id || prev.avatar,
              classTitle: getPlayerTitle(calculatedLvl, classOption.title),
              level: calculatedLvl,
              currentXP: data.xp || 0,
              totalXP: data.total_xp || 0,
              gold: data.gold || 0,
              streakDays: data.streak_days || 0,
              lastCompletedDate: data.last_completed_date || null,
              isPro: !!data.is_pro,
              interestedInPro: !!data.interested_in_pro
            };
          });
        },
        (err) => console.warn('User listener error:', err)
      );

      return () => unsubscribe();
    } catch (e) {
      console.warn('User subscription setup error:', e);
    }
  }, [currentUserId, currentScreen]);

  // ----------------------------------------------------
  // Quota-Safe Leaderboard Fetch & Ranking Logic (getDocs + 5m Cache)
  // ----------------------------------------------------
  const fetchLiveLeaderboard = useCallback(async (forceRefresh = false) => {
    const now = Date.now();
    const cached = leaderboardCacheRef.current[leaderboardTab];

    // Check if valid cache exists (< 5 minutes old) and forceRefresh is false
    if (!forceRefresh && cached && (now - cached.timestamp < LEADERBOARD_CACHE_TTL)) {
      setLeaderboardData(cached.data);
      const userIndex = cached.data.findIndex(
        (p) => p.uid === currentUserId || (player.name && p.username?.toLowerCase() === player.name?.toLowerCase())
      );
      setUserRank(userIndex !== -1 ? userIndex + 1 : (cached.data.length >= 20 ? 21 : cached.data.length + 1));
      return;
    }

    setLeaderboardLoading(true);

    try {
      const usersCol = collection(db, 'users');
      let q;

      // Single-field orderBy queries: safe for Firestore Spark free plan (requires no composite indexes)
      if (leaderboardTab === 'all_time') {
        q = query(usersCol, orderBy('total_xp', 'desc'), limit(20));
      } else {
        q = query(usersCol, orderBy('streak_days', 'desc'), limit(20));
      }

      // One-time fetch (DO NOT use continuous onSnapshot to avoid burning reads)
      const snap = await getDocs(q);
      const data: UserProfile[] = snap.docs.map((d) => d.data() as UserProfile);

      // Save to 5-minute cache
      leaderboardCacheRef.current[leaderboardTab] = {
        data,
        timestamp: now
      };
      setLastRefreshedAt(now);

      if (data.length > 0) {
        setLeaderboardData(data);

        // Find user rank in top 20
        const userIndex = data.findIndex(
          (p) => p.uid === currentUserId || (player.name && p.username?.toLowerCase() === player.name?.toLowerCase())
        );

        if (userIndex !== -1) {
          setUserRank(userIndex + 1);
        } else {
          setUserRank(data.length >= 20 ? 21 : data.length + 1);
        }
      } else {
        // Fallback: If database is new/empty, display the player's own profile as the sole row
        if (player.name) {
          const selfRow: UserProfile = {
            uid: player.id,
            username: player.name,
            username_lowercase: player.name.toLowerCase(),
            avatar_id: player.avatar,
            level: player.level,
            xp: player.currentXP,
            total_xp: player.totalXP,
            gold: player.gold,
            streak_days: player.streakDays,
            last_completed_date: player.lastCompletedDate,
            is_pro: player.isPro,
            interested_in_pro: player.interestedInPro
          };
          setLeaderboardData([selfRow]);
          setUserRank(1);
        }
      }
    } catch (e) {
      console.warn('Leaderboard fetch exception:', e);
      if (cached) {
        setLeaderboardData(cached.data);
      }
    } finally {
      setLeaderboardLoading(false);
    }
  }, [leaderboardTab, currentUserId, player.id, player.name, player.level, player.totalXP, player.avatar, player.gold, player.streakDays, player.lastCompletedDate, player.isPro, player.interestedInPro, LEADERBOARD_CACHE_TTL]);

  // Fetch or serve from 5m cache on tab switch
  useEffect(() => {
    if (activeTab === 'leaderboard') {
      fetchLiveLeaderboard(false);
    }
  }, [activeTab, leaderboardTab, fetchLiveLeaderboard]);

  // ----------------------------------------------------
  // Auth Check On Launch
  // ----------------------------------------------------
  useEffect(() => {
    setIsClient(true);
    initNativeApp();

    // Load sound and streak reminder preferences
    const savedSound = localStorage.getItem('levelup_sound');
    if (savedSound !== null) {
      setSoundEnabled(savedSound !== 'false');
    }

    const savedReminder = localStorage.getItem('levelup_reminder');
    const isReminderOn = savedReminder !== 'false';
    if (savedReminder !== null) {
      setReminderEnabled(isReminderOn);
    }
    // Schedule 9:00 PM daily streak protection reminder if active
    scheduleStreakProtectionReminder(isReminderOn);

    // Check cached player first for instantaneous offline launch
    const cachedPlayer = localStorage.getItem('levelup_player');
    if (cachedPlayer) {
      try {
        const parsed = JSON.parse(cachedPlayer);
        if (parsed.name && parsed.name.trim()) {
          setPlayer(parsed);
          setCurrentUserId(parsed.id);
        }
      } catch {}
    }

    // Subscribe to Firebase Auth state
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        setCurrentUser(user);
        setCurrentUserId(user.uid);
        await verifyUserProfile(user.uid);
      } else {
        setCurrentUser(null);
        setCurrentUserId(null);
        // If not logged in and no cached user, go to auth screen
        if (!cachedPlayer) {
          setCurrentScreen('auth');
        } else {
          // Allow viewing cached quests while offline
          setCurrentScreen('main');
        }
      }
    });

    return () => unsubscribe();
  }, [verifyUserProfile]);

  // ----------------------------------------------------
  // Auth Handlers (Email/Password & Google Sign-In)
  // ----------------------------------------------------
  const handleEmailAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    setAuthLoading(true);

    try {
      if (isSignUpMode) {
        const cred = await createUserWithEmailAndPassword(auth, authEmail.trim(), authPassword);
        if (cred.user) {
          setCurrentUser(cred.user);
          setCurrentUserId(cred.user.uid);
          showToast('Account awakened! Choose your Hunter identity.');
          setCurrentScreen('character_setup');
        }
      } else {
        const cred = await signInWithEmailAndPassword(auth, authEmail.trim(), authPassword);
        if (cred.user) {
          setCurrentUser(cred.user);
          setCurrentUserId(cred.user.uid);
          await verifyUserProfile(cred.user.uid);
        }
      }
    } catch (err: any) {
      console.error('Firebase Auth error:', err);
      let errorMsg = err.message || 'Authentication failed. Please verify credentials.';
      if (err.code === 'auth/invalid-credential' || err.code === 'auth/wrong-password') {
        errorMsg = 'Invalid email or password.';
      } else if (err.code === 'auth/email-already-in-use') {
        errorMsg = 'This email is already in use. Please sign in instead.';
      } else if (err.code === 'auth/weak-password') {
        errorMsg = 'Password must be at least 6 characters.';
      }
      setAuthError(errorMsg);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setAuthError(null);
    setAuthLoading(true);
    try {
      if (isNativePlatform()) {
        // Native Android Container: Trigger native Google account picker dialog & Credential Manager
        const result = await FirebaseAuthentication.signInWithGoogle();
        const idToken = result.credential?.idToken;

        if (idToken) {
          // Authenticate with Firebase by passing that token into signInWithCredential
          const credential = GoogleAuthProvider.credential(idToken);
          const userCred = await signInWithCredential(auth, credential);
          if (userCred.user) {
            setCurrentUser(userCred.user);
            setCurrentUserId(userCred.user.uid);
            await verifyUserProfile(userCred.user.uid);
          }
        } else if (result.user?.uid) {
          setCurrentUserId(result.user.uid);
          await verifyUserProfile(result.user.uid);
        } else {
          throw new Error('No ID token returned from native Google Sign-In.');
        }
      } else {
        // Clean Web Browser Fallback: standard web popup
        const result = await signInWithPopup(auth, googleProvider);
        if (result.user) {
          setCurrentUser(result.user);
          setCurrentUserId(result.user.uid);
          await verifyUserProfile(result.user.uid);
        }
      }
    } catch (err: any) {
      console.error('Google Sign-In error:', err);
      if (
        err.message?.includes('cancel') ||
        err.message?.includes('12501') ||
        err.code === '16' ||
        err.code === 'auth/popup-closed-by-user'
      ) {
        return;
      }
      setAuthError(err.message || 'Google Sign-In failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleOfflineBypass = () => {
    const demoId = `demo_${Date.now()}`;
    setCurrentUserId(demoId);
    setCurrentScreen('character_setup');
  };

  // ----------------------------------------------------
  // Character Creation Handler
  // ----------------------------------------------------
  const handleCharacterAwaken = async (e: React.FormEvent) => {
    e.preventDefault();
    setSetupError(null);

    const cleanName = hunterName.trim();
    if (cleanName.length < 3 || cleanName.length > 15) {
      setSetupError('Hunter name must be between 3 and 15 characters.');
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(cleanName)) {
      setSetupError('Hunter name can only contain letters, numbers, and underscores.');
      return;
    }

    setSetupLoading(true);

    try {
      const lowerName = cleanName.toLowerCase();
      const targetUserId = currentUserId || auth.currentUser?.uid || `user_${Date.now()}`;

      // Check unique username_lowercase in Firestore
      const usersCol = collection(db, 'users');
      const q = query(usersCol, where('username_lowercase', '==', lowerName), limit(1));
      const existingSnap = await getDocs(q);

      if (!existingSnap.empty && existingSnap.docs[0].id !== targetUserId) {
        setSetupError('This Hunter name is already claimed by another operative. Choose another.');
        setSetupLoading(false);
        return;
      }

      const selectedClass = AVATAR_OPTIONS[selectedAvatarIdx] || AVATAR_OPTIONS[0];

      const newProfileData: UserProfile = {
        uid: targetUserId,
        username: cleanName,
        username_lowercase: lowerName,
        avatar_id: selectedClass.icon,
        level: 1,
        xp: 0,
        total_xp: 0,
        gold: 0,
        streak_days: 0,
        last_completed_date: null,
        is_pro: false,
        interested_in_pro: false,
        created_at: new Date().toISOString()
      };

      // Save to Firestore users/{uid}
      await setDoc(doc(db, 'users', targetUserId), newProfileData, { merge: true });

      const initializedPlayer: PlayerStats = {
        id: targetUserId,
        name: cleanName,
        avatar: selectedClass.icon,
        classTitle: getPlayerTitle(1, selectedClass.title),
        level: 1,
        currentXP: 0,
        totalXP: 0,
        gold: 0,
        streakDays: 0,
        lastCompletedDate: null,
        isPro: false,
        interestedInPro: false,
        unlockedBadgeIds: ['first_blood']
      };

      setPlayer(initializedPlayer);
      localStorage.setItem('levelup_player', JSON.stringify(initializedPlayer));

      playLevelUpSound(false);
      confetti({ particleCount: 100, spread: 80, origin: { y: 0.5 } });

      showToast(`System Awakened! Welcome Hunter ${cleanName}.`);
      setCurrentScreen('main');
    } catch (err: any) {
      console.error('Character awaken error:', err);
      // Fallback for offline or local preview
      const selectedClass = AVATAR_OPTIONS[selectedAvatarIdx] || AVATAR_OPTIONS[0];
      const targetUserId = currentUserId || `user_${Date.now()}`;
      const fallbackPlayer: PlayerStats = {
        id: targetUserId,
        name: cleanName,
        avatar: selectedClass.icon,
        classTitle: getPlayerTitle(1, selectedClass.title),
        level: 1,
        currentXP: 0,
        totalXP: 0,
        gold: 0,
        streakDays: 0,
        lastCompletedDate: null,
        isPro: false,
        interestedInPro: false,
        unlockedBadgeIds: ['first_blood']
      };
      setPlayer(fallbackPlayer);
      localStorage.setItem('levelup_player', JSON.stringify(fallbackPlayer));
      setCurrentScreen('main');
    } finally {
      setSetupLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await signOut(auth);
    } catch {}
    localStorage.removeItem('levelup_player');
    localStorage.removeItem('levelup_habits');
    setCurrentUserId(null);
    setCurrentUser(null);
    setIsSettingsModal(false);
    setCurrentScreen('auth');
    triggerHaptic('light');
    showToast('Signed out of LEVEL UP.');
  };

  const handleToggleSound = () => {
    const next = !soundEnabled;
    setSoundEnabled(next);
    localStorage.setItem('levelup_sound', String(next));
    triggerHaptic('light');
    showToast(next ? 'Sound effects enabled' : 'Sound effects muted');
  };

  const handleToggleReminder = async () => {
    const next = !reminderEnabled;
    setReminderEnabled(next);
    localStorage.setItem('levelup_reminder', String(next));
    await scheduleStreakProtectionReminder(next);
    triggerHaptic('light');
    showToast(next ? 'Daily 9:00 PM streak reminder active' : 'Streak reminder deactivated');
  };

  // 1-Tap Student Starter Quest Quick Add
  const handleAddStarterQuest = async (sq: typeof STARTER_QUESTS[0]) => {
    triggerHaptic('light');
    if (!player.isPro && habits.length >= MAX_FREE_HABITS) {
      showToast(`Quest slots full (${MAX_FREE_HABITS}/${MAX_FREE_HABITS}). Upgrade slots or manage existing quests.`);
      return;
    }

    const newHabitData: HabitDocument = {
      title: sq.name,
      difficulty: sq.difficulty,
      icon: sq.icon,
      completed_dates: [],
      created_at: new Date().toISOString()
    };

    if (currentUserId && currentUserId !== 'user_init') {
      try {
        const docRef = await addDoc(collection(db, 'users', currentUserId, 'habits'), newHabitData);
        const newHabit: Habit = {
          id: docRef.id,
          name: sq.name,
          icon: sq.icon,
          difficulty: sq.difficulty,
          xpReward: sq.xpReward,
          goldReward: sq.goldReward,
          completedDates: []
        };
        setHabits((prev) => [newHabit, ...prev]);
      } catch (err) {
        console.warn('Starter quest add error:', err);
        const tempId = `quest-${Date.now()}`;
        setHabits((prev) => [
          {
            id: tempId,
            name: sq.name,
            icon: sq.icon,
            difficulty: sq.difficulty,
            xpReward: sq.xpReward,
            goldReward: sq.goldReward,
            completedDates: []
          },
          ...prev
        ]);
      }
    } else {
      const tempId = `quest-${Date.now()}`;
      setHabits((prev) => [
        {
          id: tempId,
          name: sq.name,
          icon: sq.icon,
          difficulty: sq.difficulty,
          xpReward: sq.xpReward,
          goldReward: sq.goldReward,
          completedDates: []
        },
        ...prev
      ]);
    }

    playCoinSound(!soundEnabled);
    showToast(`⚔️ Quest Enlisted: "${sq.name}"`);
  };

  // Google Play Store Mandatory Account & Data Deletion Flow
  const handleDeleteAccountAndData = async () => {
    setIsDeletingAccount(true);
    triggerHaptic('warning');
    try {
      const userToDelete = auth.currentUser;
      const uidToDelete = currentUserId || userToDelete?.uid;

      if (uidToDelete && uidToDelete !== 'user_init') {
        // 1. Delete habits subcollection
        try {
          const habitsSnap = await getDocs(collection(db, 'users', uidToDelete, 'habits'));
          for (const hDoc of habitsSnap.docs) {
            await deleteDoc(doc(db, 'users', uidToDelete, 'habits', hDoc.id)).catch(() => {});
          }
        } catch (habitsErr) {
          console.warn('Habits deletion warning:', habitsErr);
        }

        // 2. Delete rewards subcollection if exists
        try {
          const rewardsSnap = await getDocs(collection(db, 'users', uidToDelete, 'rewards'));
          for (const rDoc of rewardsSnap.docs) {
            await deleteDoc(doc(db, 'users', uidToDelete, 'rewards', rDoc.id)).catch(() => {});
          }
        } catch (rewardsErr) {
          console.warn('Rewards deletion warning:', rewardsErr);
        }

        // 3. Delete user document from Cloud Firestore
        await deleteDoc(doc(db, 'users', uidToDelete)).catch(() => {});
      }

      // 4. Delete user from Firebase Auth
      if (userToDelete) {
        try {
          await deleteUser(userToDelete);
        } catch (authErr: any) {
          if (authErr.code === 'auth/requires-recent-login') {
            showToast('Security verification required: Please re-login and retry account deletion.');
            setIsDeletingAccount(false);
            setIsDeleteAccountModal(false);
            return;
          }
          console.warn('Auth user delete error:', authErr);
        }
      }

      // 5. Purge local storage and reset state
      localStorage.removeItem('levelup_player');
      localStorage.removeItem('levelup_habits');
      localStorage.removeItem('levelup_sound');
      localStorage.removeItem('levelup_reminder');

      setCurrentUser(null);
      setCurrentUserId(null);
      setIsDeleteAccountModal(false);
      setIsSettingsModal(false);
      setCurrentScreen('auth');
      triggerHaptic('success');
      showToast('Account and all associated hunter data permanently purged.');
    } catch (err: any) {
      console.error('Account deletion error:', err);
      showToast(err.message || 'Error deleting account. Please contact support.');
    } finally {
      setIsDeletingAccount(false);
    }
  };

  // ----------------------------------------------------
  // Habit (Quest) Completion / Uncheck with Atomic Firestore increment()
  // ----------------------------------------------------
  const handleToggleHabit = async (habitId: string, dateKey: string, e?: React.MouseEvent) => {
    triggerHaptic('light');

    const targetHabit = habits.find((h) => h.id === habitId);
    if (!targetHabit) return;

    const wasCompleted = targetHabit.completedDates.includes(dateKey);
    const willBeCompleted = !wasCompleted;

    // Optimistic local state update
    const updatedHabits = habits.map((h) => {
      if (h.id !== habitId) return h;
      return {
        ...h,
        completedDates: willBeCompleted
          ? [...new Set([...h.completedDates, dateKey])]
          : h.completedDates.filter((d) => d !== dateKey)
      };
    });
    setHabits(updatedHabits);

    if (willBeCompleted) {
      playQuestCompleteSound(!soundEnabled);
      const posX = e?.clientX;
      const posY = e?.clientY;
      spawnParticle(`+${targetHabit.xpReward} XP!`, '#3B82F6', posX, posY);

      // Streak calculation
      let newStreak = player.streakDays;
      if (dateKey === todayKey) {
        if (player.lastCompletedDate === yesterdayKey) {
          newStreak = player.streakDays + 1;
        } else if (player.lastCompletedDate !== todayKey) {
          newStreak = 1;
        }
      }

      const newTotalXP = player.totalXP + targetHabit.xpReward;
      const newLevel = calculateLevel(newTotalXP);
      const newGold = player.gold + targetHabit.goldReward;

      // Check level up celebration
      if (newLevel > player.level) {
        const baseRole = player.classTitle.split(' ').pop() || 'Hunter';
        const newTitle = getPlayerTitle(newLevel, baseRole);
        setLevelUpData({ newLevel, oldLevel: player.level, title: newTitle });
        setIsLevelUpModal(true);
        triggerHaptic('heavy');
        playLevelUpSound(!soundEnabled);
        confetti({ particleCount: 90, spread: 80, origin: { y: 0.5 } });
      }

      setPlayer((prev) => ({
        ...prev,
        level: newLevel,
        currentXP: prev.currentXP + targetHabit.xpReward,
        totalXP: newTotalXP,
        gold: newGold,
        streakDays: newStreak,
        lastCompletedDate: dateKey === todayKey ? todayKey : prev.lastCompletedDate
      }));

      showToast(`+${targetHabit.xpReward} XP & +${targetHabit.goldReward} Gold earned!`);

      // Sync atomically to Firestore if logged in
      if (currentUserId && currentUserId !== 'user_init') {
        try {
          // 1. Update habit document
          const habitDocRef = doc(db, 'users', currentUserId, 'habits', habitId);
          await updateDoc(habitDocRef, {
            completed_dates: arrayUnion(dateKey)
          });

          // 2. Increment user XP, total_xp, and gold
          const userDocRef = doc(db, 'users', currentUserId);
          await updateDoc(userDocRef, {
            xp: increment(targetHabit.xpReward),
            total_xp: increment(targetHabit.xpReward),
            gold: increment(targetHabit.goldReward),
            level: newLevel,
            streak_days: newStreak,
            last_completed_date: dateKey === todayKey ? todayKey : (player.lastCompletedDate || todayKey)
          });
        } catch (err) {
          console.warn('Firestore habit completion sync exception:', err);
        }
      }
    } else {
      // Unchecking habit completed today: Decrement XP and Gold so users cannot farm XP
      const penaltyXP = targetHabit.xpReward;
      const penaltyGold = targetHabit.goldReward;

      const newTotalXP = Math.max(0, player.totalXP - penaltyXP);
      const newLevel = calculateLevel(newTotalXP);
      const newGold = Math.max(0, player.gold - penaltyGold);

      setPlayer((prev) => ({
        ...prev,
        level: newLevel,
        currentXP: Math.max(0, prev.currentXP - penaltyXP),
        totalXP: newTotalXP,
        gold: newGold
      }));

      showToast('Quest unchecked.');

      if (currentUserId && currentUserId !== 'user_init') {
        try {
          // 1. Remove from habit completed_dates
          const habitDocRef = doc(db, 'users', currentUserId, 'habits', habitId);
          await updateDoc(habitDocRef, {
            completed_dates: arrayRemove(dateKey)
          });

          // 2. Decrement user XP, total_xp, and gold atomically and clamped to >= 0
          const userDocRef = doc(db, 'users', currentUserId);
          await updateDoc(userDocRef, {
            xp: Math.max(0, player.currentXP - penaltyXP),
            total_xp: newTotalXP,
            gold: newGold,
            level: newLevel
          });
        } catch (err) {
          console.warn('Firestore habit uncheck sync exception:', err);
        }
      }
    }
  };

  const handleMarkAllToday = async () => {
    const uncompletedHabits = habits.filter((h) => !h.completedDates.includes(todayKey));
    if (uncompletedHabits.length === 0) {
      showToast('All quests for today are already completed!');
      return;
    }

    let addedXP = 0;
    let addedGold = 0;
    for (const h of uncompletedHabits) {
      addedXP += h.xpReward;
      addedGold += h.goldReward;
    }

    playLevelUpSound(!soundEnabled);
    triggerHaptic('success');
    spawnParticle(`ALL QUESTS COMPLETED! 🔥`, '#F5B041');
    confetti({ particleCount: 70, spread: 70, origin: { y: 0.6 } });

    // Mark all locally
    setHabits((prev) =>
      prev.map((h) => ({
        ...h,
        completedDates: [...new Set([...h.completedDates, todayKey])]
      }))
    );

    let newStreak = player.streakDays;
    if (player.lastCompletedDate === yesterdayKey) {
      newStreak = player.streakDays + 1;
    } else if (player.lastCompletedDate !== todayKey) {
      newStreak = 1;
    }

    const newTotalXP = player.totalXP + addedXP;
    const newLevel = calculateLevel(newTotalXP);
    const newGold = player.gold + addedGold;

    setPlayer((prev) => ({
      ...prev,
      level: newLevel,
      currentXP: prev.currentXP + addedXP,
      totalXP: newTotalXP,
      gold: newGold,
      streakDays: newStreak,
      lastCompletedDate: todayKey
    }));

    showToast(`Tactical Surge: Completed ${uncompletedHabits.length} quests!`);

    if (currentUserId && currentUserId !== 'user_init') {
      try {
        for (const h of uncompletedHabits) {
          const habitDocRef = doc(db, 'users', currentUserId, 'habits', h.id);
          updateDoc(habitDocRef, { completed_dates: arrayUnion(todayKey) }).catch(() => {});
        }
        const userDocRef = doc(db, 'users', currentUserId);
        await updateDoc(userDocRef, {
          xp: increment(addedXP),
          total_xp: increment(addedXP),
          gold: increment(addedGold),
          level: newLevel,
          streak_days: newStreak,
          last_completed_date: todayKey
        });
      } catch (err) {
        console.warn('Batch mark all exception:', err);
      }
    }
  };

  const handleCreateQuest = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanTitle = newQuestName.trim().slice(0, 100);
    if (!cleanTitle) {
      showToast('Quest title cannot be empty.');
      return;
    }

    // Limit free users to 5 active habits (X/5 Active Quest Slots)
    if (!player.isPro && habits.length >= MAX_FREE_HABITS) {
      showToast(`Quest slots full (${MAX_FREE_HABITS}/${MAX_FREE_HABITS}). Upgrade slots or manage existing quests.`);
      return;
    }

    const diffReward = DIFFICULTY_MAP[newQuestDifficulty];
    const newHabitData: HabitDocument = {
      title: cleanTitle,
      difficulty: newQuestDifficulty,
      icon: newQuestIcon,
      completed_dates: [],
      created_at: new Date().toISOString()
    };

    if (currentUserId && currentUserId !== 'user_init') {
      try {
        const docRef = await addDoc(collection(db, 'users', currentUserId, 'habits'), newHabitData);
        const newHabit: Habit = {
          id: docRef.id,
          name: cleanTitle,
          icon: newHabitData.icon,
          difficulty: newHabitData.difficulty,
          xpReward: diffReward.xp,
          goldReward: diffReward.gold,
          completedDates: []
        };
        setHabits((prev) => [newHabit, ...prev]);
      } catch (err) {
        console.warn('Firestore create habit error:', err);
        const tempId = `quest-${Date.now()}`;
        const newHabit: Habit = {
          id: tempId,
          name: cleanTitle,
          icon: newHabitData.icon,
          difficulty: newHabitData.difficulty,
          xpReward: diffReward.xp,
          goldReward: diffReward.gold,
          completedDates: []
        };
        setHabits((prev) => [newHabit, ...prev]);
      }
    } else {
      const tempId = `quest-${Date.now()}`;
      const newHabit: Habit = {
        id: tempId,
        name: cleanTitle,
        icon: newHabitData.icon,
        difficulty: newHabitData.difficulty,
        xpReward: diffReward.xp,
        goldReward: diffReward.gold,
        completedDates: []
      };
      setHabits((prev) => [newHabit, ...prev]);
    }

    setNewQuestName('');
    setIsAddQuestModal(false);
    playCoinSound(!soundEnabled);
    triggerHaptic('light');
    showToast(`⚔️ Quest Enlisted: "${cleanTitle}"`);
  };

  const handleOpenEditQuest = (habit: Habit) => {
    setEditingHabit(habit);
    setEditQuestName(habit.name);
    setEditQuestIcon(habit.icon);
    setEditQuestDifficulty(habit.difficulty);
    triggerHaptic('light');
  };

  const handleUpdateQuest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingHabit) return;

    const cleanTitle = editQuestName.trim().slice(0, 100);
    if (!cleanTitle) {
      showToast('Quest title cannot be empty.');
      return;
    }

    const diffReward = DIFFICULTY_MAP[editQuestDifficulty];
    setHabits((prev) =>
      prev.map((h) => {
        if (h.id !== editingHabit.id) return h;
        return {
          ...h,
          name: cleanTitle,
          icon: editQuestIcon,
          difficulty: editQuestDifficulty,
          xpReward: diffReward.xp,
          goldReward: diffReward.gold
        };
      })
    );

    if (currentUserId && currentUserId !== 'user_init') {
      try {
        const habitDocRef = doc(db, 'users', currentUserId, 'habits', editingHabit.id);
        await updateDoc(habitDocRef, {
          title: cleanTitle,
          difficulty: editQuestDifficulty,
          icon: editQuestIcon
        });
      } catch (err) {
        console.warn('Update quest error:', err);
      }
    }

    setEditingHabit(null);
    triggerHaptic('light');
    showToast(`Quest updated: "${cleanTitle}"`);
  };

  const handleDeleteQuest = async (id: string, name: string) => {
    setHabits((prev) => prev.filter((h) => h.id !== id));
    if (currentUserId && currentUserId !== 'user_init') {
      try {
        await deleteDoc(doc(db, 'users', currentUserId, 'habits', id));
      } catch (err) {
        console.warn('Delete quest error:', err);
      }
    }
    showToast(`Removed quest "${name}"`);
  };

  const handleClaimReward = (reward: RewardItem) => {
    if (player.gold < reward.cost) {
      showToast(`Not enough Gold! Need ${reward.cost - player.gold} more gold.`);
      return;
    }

    const nextGold = player.gold - reward.cost;
    setPlayer((prev) => ({ ...prev, gold: nextGold }));

    if (currentUserId && currentUserId !== 'user_init') {
      updateDoc(doc(db, 'users', currentUserId), { gold: increment(-reward.cost) }).catch(() => {});
    }

    setRewards((prev) =>
      prev.map((r) => (r.id === reward.id ? { ...r, claimedCount: r.claimedCount + 1 } : r))
    );

    triggerHaptic('success');
    playCoinSound(!soundEnabled);
    spawnParticle(`REWARD CLAIMED! 🎁`, '#F5B041');
    showToast(`Unlocked: "${reward.name}"!`);
  };

  const handleAddCustomReward = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRewardName.trim()) return;

    const newR: RewardItem = {
      id: `reward-${Date.now()}`,
      name: newRewardName.trim(),
      icon: newRewardIcon,
      cost: Number(newRewardCost) || 50,
      claimedCount: 0,
      category: 'custom'
    };

    setRewards((prev) => [...prev, newR]);
    setNewRewardName('');
    setIsAddRewardModal(false);
    triggerHaptic('light');
    playCoinSound(!soundEnabled);
    showToast(`Custom reward added to Loot Shop!`);
  };

  // Notify Me on Launch CTA
  const handleNotifyPro = async () => {
    setPlayer((prev) => ({ ...prev, interestedInPro: true }));
    if (currentUserId && currentUserId !== 'user_init') {
      try {
        await updateDoc(doc(db, 'users', currentUserId), { interested_in_pro: true });
      } catch (err) {
        console.warn('Update interested_in_pro error:', err);
      }
    }
    playCoinSound(!soundEnabled);
    triggerHaptic('light');
    showToast('⚔️ Preference saved! We will notify you when Level Up Pro launches.');
  };

  // ----------------------------------------------------
  // RENDER: 1. Loading Screen
  // ----------------------------------------------------
  if (!isClient || currentScreen === 'loading') {
    return (
      <div className="min-h-screen bg-[#0A0D14] flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#F5B041] border-t-transparent rounded-full animate-spin" />
          <span className="text-[11px] font-bold tracking-widest uppercase text-[#F5B041]">
            INITIALIZING LEVEL UP SYSTEM...
          </span>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // RENDER: 2. Minimalist Gaming Auth Screen ("System Awakening")
  // ----------------------------------------------------
  if (currentScreen === 'auth') {
    return (
      <div className="min-h-screen bg-[#0A0D14] text-slate-100 flex flex-col items-center justify-center p-4 relative selection:bg-[#F5B041]/30">
        <div className="w-full max-w-sm flex flex-col space-y-5 animate-in fade-in duration-300">
          {/* System Awakening Header */}
          <div className="text-center space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#121722] border border-[#1E2638] text-[10px] font-black tracking-widest uppercase text-[#F5B041]">
              <Sparkles className="w-3 h-3" />
              <span>SYSTEM AWAKENING PROTOCOL</span>
            </div>

            <div className="w-14 h-14 mx-auto rounded-2xl bg-[#121722] border-2 border-[#F5B041] flex items-center justify-center text-2xl shadow-lg shadow-[#F5B041]/15 my-2">
              👑
            </div>

            <h1 className="text-2xl font-black tracking-wider text-white">LEVEL UP</h1>
            <p className="text-xs text-slate-400 max-w-xs mx-auto leading-relaxed">
              Gamify your life. Sign in to synchronize your RPG Hunter progress and daily habit quests.
            </p>
          </div>

          {/* Auth Card */}
          <div className="p-5 rounded-2xl bg-[#121722] border border-[#1E2638] shadow-xl space-y-4">
            {/* Mode Switcher */}
            <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-[#0A0D14] border border-[#1E2638]">
              <button
                type="button"
                onClick={() => {
                  setIsSignUpMode(false);
                  setAuthError(null);
                }}
                className={`py-1.5 rounded-lg text-xs font-bold transition ${
                  !isSignUpMode
                    ? 'bg-[#F5B041] text-[#0A0D14] shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => {
                  setIsSignUpMode(true);
                  setAuthError(null);
                }}
                className={`py-1.5 rounded-lg text-xs font-bold transition ${
                  isSignUpMode
                    ? 'bg-[#F5B041] text-[#0A0D14] shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Error Message */}
            {authError && (
              <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="leading-tight">{authError}</span>
              </div>
            )}

            {/* Email / Password Form */}
            <form onSubmit={handleEmailAuth} className="space-y-3">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Hunter Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="email"
                    required
                    placeholder="hunter@levelup.app"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Access Code / Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    className="w-full pl-9 pr-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full py-2.5 rounded-xl bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14] font-black text-xs uppercase tracking-wider shadow-sm flex items-center justify-center gap-1.5 transition active:scale-95 disabled:opacity-50"
              >
                {authLoading ? (
                  <div className="w-4 h-4 border-2 border-[#0A0D14] border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{isSignUpMode ? 'Initialize Hunter Account' : 'Enter the System'}</span>
                    <ArrowRight className="w-3.5 h-3.5 stroke-[3]" />
                  </>
                )}
              </button>
            </form>

            {/* Google Gateway */}
            <div className="relative flex py-1 items-center">
              <div className="flex-grow border-t border-[#1E2638]" />
              <span className="flex-shrink mx-2 text-[10px] font-bold uppercase text-slate-500 tracking-wider">
                OR PROTOCOL
              </span>
              <div className="flex-grow border-t border-[#1E2638]" />
            </div>

            <button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={authLoading}
              className="w-full py-2.5 rounded-xl bg-[#0A0D14] hover:bg-[#1E2638] border border-[#1E2638] text-slate-200 text-xs font-bold flex items-center justify-center gap-2 transition active:scale-95 disabled:opacity-50"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.7-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 12 0 14.5s.7 4.8 1.9 7.2l3.7-2.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 17C3.7 20.7 7.5 24 12 24z"
                />
              </svg>
              <span>Continue with Google</span>
            </button>
          </div>

          {/* Offline / Local Testing Bypass */}
          <div className="text-center pt-1">
            <button
              type="button"
              onClick={handleOfflineBypass}
              className="text-[11px] text-slate-500 hover:text-[#F5B041] transition"
            >
              Skip & Play Offline (Demo Hunter Mode) →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // RENDER: 3. Character Creation Screen (First-Time Users)
  // ----------------------------------------------------
  if (currentScreen === 'character_setup') {
    return (
      <div className="min-h-screen bg-[#0A0D14] text-slate-100 flex flex-col items-center justify-center p-4 relative selection:bg-[#F5B041]/30">
        <div className="w-full max-w-sm flex flex-col space-y-4 animate-in fade-in duration-300">
          <div className="text-center space-y-1.5">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#121722] border border-[#1E2638] text-[10px] font-black tracking-widest uppercase text-[#3B82F6]">
              <ShieldCheck className="w-3 h-3 text-[#3B82F6]" />
              <span>NEW OPERATIVE REGISTRATION</span>
            </div>

            <h1 className="text-xl font-black text-white">Awaken Your Character</h1>
            <p className="text-xs text-slate-400 max-w-xs mx-auto">
              Choose your Hunter identity and select your starting class.
            </p>
          </div>

          <form onSubmit={handleCharacterAwaken} className="p-5 rounded-2xl bg-[#121722] border border-[#1E2638] shadow-xl space-y-4">
            {/* Error Message */}
            {setupError && (
              <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span className="leading-tight">{setupError}</span>
              </div>
            )}

            {/* Hunter Name Input */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Hunter Name / Username
                </label>
                <span className="text-[10px] text-slate-500">{hunterName.length}/15</span>
              </div>
              <input
                type="text"
                required
                maxLength={15}
                placeholder="e.g. Valkyrie, IronClad, Phoenix..."
                value={hunterName}
                onChange={(e) => setHunterName(e.target.value.replace(/[^a-zA-Z0-9_]/g, ''))}
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs font-bold focus:outline-none focus:border-[#F5B041]"
              />
              <span className="text-[10px] text-slate-500 mt-1 block">
                3–15 characters (letters, numbers, underscores)
              </span>
            </div>

            {/* Starting Class Selection (6 Class Icons) */}
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                Select Starting Class
              </label>
              <div className="grid grid-cols-2 gap-2">
                {AVATAR_OPTIONS.map((av, idx) => {
                  const isSelected = selectedAvatarIdx === idx;
                  return (
                    <button
                      key={av.title}
                      type="button"
                      onClick={() => setSelectedAvatarIdx(idx)}
                      className={`p-2.5 rounded-xl border text-left flex items-center gap-2.5 transition active:scale-95 ${
                        isSelected
                          ? 'bg-[#0A0D14] border-[#F5B041] shadow-sm shadow-[#F5B041]/10'
                          : 'bg-[#0A0D14]/60 border-[#1E2638] opacity-75 hover:opacity-100'
                      }`}
                    >
                      <div className="text-2xl shrink-0">{av.icon}</div>
                      <div className="min-w-0 flex-1">
                        <div className={`text-xs font-black break-words leading-tight ${isSelected ? 'text-[#F5B041]' : 'text-slate-200'}`}>
                          {av.title}
                        </div>
                        <div className="text-[9px] text-slate-400 break-words leading-tight mt-0.5">{av.role}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Primary Gold CTA Button */}
            <button
              type="submit"
              disabled={setupLoading || hunterName.trim().length < 3}
              className="w-full py-3 rounded-xl bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14] font-black text-xs uppercase tracking-wider shadow-md shadow-[#F5B041]/20 flex items-center justify-center gap-1.5 transition active:scale-95 disabled:opacity-50"
            >
              {setupLoading ? (
                <div className="w-4 h-4 border-2 border-[#0A0D14] border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Sparkles className="w-4 h-4 stroke-[2.5]" />
                  <span>Awaken & Start Quests</span>
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // ----------------------------------------------------
  // RENDER: 4. Main App (Quests, Leaderboard, Shop, Profile)
  // ----------------------------------------------------
  return (
    <div className="min-h-screen bg-[#0A0D14] text-slate-100 flex flex-col items-center justify-start relative selection:bg-[#F5B041]/30 selection:text-[#F5B041]">
      {/* Floating XP / Gold Particles */}
      {particles.map((p) => (
        <div
          key={p.id}
          className="fixed pointer-events-none z-50 text-sm font-black tracking-wide drop-shadow-[0_2px_8px_rgba(0,0,0,0.9)] animate-float-xp"
          style={{ left: `${p.x - 25}px`, top: `${p.y - 20}px`, color: p.color }}
        >
          {p.text}
        </div>
      ))}

      {/* Floating Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 bg-[#121722]/95 border border-[#1E2638] text-slate-100 px-4 py-2 rounded-full shadow-2xl backdrop-blur-md animate-level-burst text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />
          <span className="break-words">{toastMessage}</span>
        </div>
      )}

      {/* Smartphone Container Viewport */}
      <div className="w-full max-w-md min-h-screen bg-[#0A0D14] flex flex-col relative pb-20">
        {/* ======================================================== */}
        {/* TOP STATUS HUD (Compact, Single-Line, Quests Tab Only)    */}
        {/* ======================================================== */}
        {activeTab === 'quests' && (
          <header className="sticky top-0 z-40 bg-[#0A0D14]/95 backdrop-blur-md border-b border-[#1E2638] px-4 py-2.5">
            <div className="flex items-center justify-between gap-3">
              {/* Left: Avatar + Username + Lv + Sleek thin XP Progress Bar */}
              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                <div className="relative shrink-0">
                  <div className="w-9 h-9 rounded-xl bg-[#121722] border border-[#1E2638] flex items-center justify-center text-lg shadow-sm">
                    {player.avatar}
                  </div>
                  <span className="absolute -bottom-1 -right-1 px-1 py-0.2 rounded bg-[#F5B041] text-[#0A0D14] text-[9px] font-black leading-tight shadow-sm">
                    {player.level}
                  </span>
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 leading-tight">
                    <span className="text-xs font-bold text-slate-100 break-words leading-tight">{player.name}</span>
                    <span className="text-[10px] text-slate-400 font-semibold shrink-0">Lv.{player.level}</span>
                    {player.isPro && (
                      <Crown className="w-3 h-3 text-[#F5B041] shrink-0" />
                    )}
                  </div>
                  {/* Sleek Thin XP Progress Bar */}
                  <div className="w-full max-w-[130px] h-1.5 bg-[#121722] border border-[#1E2638] rounded-full overflow-hidden mt-1">
                    <div
                      className="h-full bg-gradient-to-r from-[#3B82F6] to-[#F5B041] rounded-full transition-all duration-300"
                      style={{ width: `${xpPercentage}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Right: Streak Count (🔥 Xd) + Gold Balance */}
              <div className="flex items-center gap-2 shrink-0">
                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#121722] border border-[#1E2638] text-[#F5B041] text-xs font-bold shadow-sm">
                  <Flame className="w-3.5 h-3.5 fill-[#F5B041]" />
                  <span>{player.streakDays}d</span>
                </div>

                <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#121722] border border-[#1E2638] text-[#F5B041] text-xs font-bold shadow-sm">
                  <span className="text-sm">🪙</span>
                  <span>{player.gold}</span>
                </div>
              </div>
            </div>
          </header>
        )}

        {/* ======================================================== */}
        {/* MAIN CONTENT AREA                                        */}
        {/* ======================================================== */}
        <main className="flex-1 px-4 py-3 space-y-3.5">
          {/* -------------------------------------------------------- */}
          {/* TAB 1: QUESTS (HOME)                                     */}
          {/* -------------------------------------------------------- */}
          {activeTab === 'quests' && (
            <div className="space-y-3.5">
              {/* Minimalist Horizontal 7-Day Calendar Strip */}
              <div className="bg-[#121722] border border-[#1E2638] rounded-2xl p-2.5 shadow-sm">
                <div className="flex items-center justify-between mb-2 px-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300">
                    <Calendar className="w-3.5 h-3.5 text-[#F5B041]" />
                    <span>
                      {weekDays[0].monthShort} {weekDays[0].dayNumber} – {weekDays[6].dayNumber}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setWeekOffset((o) => o - 1)}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-[#1E2638] transition"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    {weekOffset !== 0 && (
                      <button
                        onClick={() => setWeekOffset(0)}
                        className="text-[10px] px-2 py-0.5 rounded bg-[#F5B041]/10 text-[#F5B041] border border-[#F5B041]/20 font-bold"
                      >
                        Today
                      </button>
                    )}
                    <button
                      onClick={() => setWeekOffset((o) => Math.min(0, o + 1))}
                      disabled={weekOffset === 0}
                      className={`p-1 rounded-lg transition ${
                        weekOffset === 0 ? 'text-slate-700' : 'text-slate-400 hover:text-white hover:bg-[#1E2638]'
                      }`}
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Day Buttons */}
                <div className="grid grid-cols-7 gap-1">
                  {weekDays.map((day) => {
                    const completedOnDay = habits.filter((h) => h.completedDates.includes(day.dateKey)).length;
                    const isAllDone = completedOnDay === habits.length && habits.length > 0;

                    return (
                      <div
                        key={day.dateKey}
                        className={`flex flex-col items-center py-2 px-1 rounded-xl text-center transition ${
                          day.isToday
                            ? 'bg-[#F5B041]/10 border border-[#F5B041]/40 text-[#F5B041]'
                            : 'bg-[#0A0D14]/70 border border-[#1E2638]/70 text-slate-400'
                        }`}
                      >
                        <span className="text-[9px] uppercase font-bold tracking-wider">{day.dayShort}</span>
                        <span className={`text-xs font-black mt-0.5 ${day.isToday ? 'text-[#F5B041]' : 'text-slate-200'}`}>
                          {day.dayNumber}
                        </span>
                        <div className="mt-1 flex items-center justify-center">
                          {isAllDone ? (
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-sm" />
                          ) : completedOnDay > 0 ? (
                            <span className="w-1.5 h-1.5 rounded-full bg-[#F5B041]" />
                          ) : (
                            <span className="w-1.5 h-1.5 rounded-full bg-slate-800" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Slot Indicator & Quick Surge Action */}
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Daily Quests
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#121722] text-[#F5B041] border border-[#1E2638] font-bold">
                    {habits.length}/{MAX_FREE_HABITS} Active Quest Slots
                  </span>
                </div>

                {habits.length > 0 && (
                  <button
                    onClick={handleMarkAllToday}
                    className="px-2.5 py-1 rounded-xl text-[11px] font-bold bg-[#121722] hover:bg-[#1E2638] text-slate-300 border border-[#1E2638] flex items-center gap-1 active:scale-95 transition"
                    title="Mark all habits completed for today"
                  >
                    <Zap className="w-3 h-3 text-[#F5B041]" />
                    <span>Complete All</span>
                  </button>
                )}
              </div>

              {/* Habit Checklist Cards directly following Calendar */}
              <div className="space-y-2">
                {habits.length === 0 ? (
                  <div className="py-8 px-4 rounded-2xl bg-[#121722] border border-[#1E2638] text-center space-y-4 shadow-sm">
                    <div className="w-12 h-12 rounded-2xl bg-[#0A0D14] border border-[#1E2638] flex items-center justify-center mx-auto text-2xl text-[#F5B041]">
                      ⚔️
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">Your Quest Book is Ready!</h3>
                      <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
                        Tap the <span className="text-[#F5B041] font-bold">+ button</span> or 1-tap enlist recommended student starter quests below to start leveling up.
                      </p>
                    </div>

                    {/* 1-Tap Quick-Add Starter Quests */}
                    {STARTER_QUESTS.filter((sq) => !habits.some((h) => h.name.toLowerCase() === sq.name.toLowerCase())).length > 0 && (
                      <div className="pt-3 text-left space-y-2 border-t border-[#1E2638]/70">
                        <div className="flex items-center justify-between px-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#F5B041] flex items-center gap-1">
                            <Sparkles className="w-3 h-3 text-[#F5B041]" />
                            <span>Quick-Add Starter Quests</span>
                          </span>
                          <span className="text-[10px] text-slate-500 font-semibold">1-Tap Enlist</span>
                        </div>

                        <div className="grid grid-cols-1 gap-2">
                          {STARTER_QUESTS.filter((sq) => !habits.some((h) => h.name.toLowerCase() === sq.name.toLowerCase())).map((sq) => (
                            <button
                              key={sq.name}
                              type="button"
                              onClick={() => handleAddStarterQuest(sq)}
                              className="p-2.5 rounded-xl bg-[#0A0D14] hover:bg-[#161D2B] border border-[#1E2638] hover:border-[#F5B041]/40 text-left flex items-center justify-between gap-3 transition active:scale-98 group"
                            >
                              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                                <span className="text-xl shrink-0">{sq.icon}</span>
                                <div className="min-w-0 flex-1">
                                  <div className="text-xs font-bold text-slate-200 group-hover:text-white break-words leading-tight">
                                    {sq.name}
                                  </div>
                                  <div className="text-[10px] text-slate-400 flex items-center gap-1.5 mt-0.5">
                                    <span className="capitalize text-slate-400 font-medium">{sq.difficulty}</span>
                                    <span>•</span>
                                    <span className="text-[#3B82F6] font-semibold">+{sq.xpReward} XP</span>
                                    <span>•</span>
                                    <span className="text-[#F5B041] font-semibold">+{sq.goldReward}g</span>
                                  </div>
                                </div>
                              </div>
                              <div className="w-7 h-7 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-[#F5B041] shrink-0 group-hover:bg-[#F5B041] group-hover:text-[#0A0D14] transition shadow-sm">
                                <Plus className="w-4 h-4 stroke-[2.5]" />
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  habits.map((habit) => {
                    const isDoneToday = habit.completedDates.includes(todayKey);

                    return (
                      <div
                        key={habit.id}
                        className={`rounded-2xl border transition-all duration-200 ${
                          isDoneToday
                            ? 'bg-[#121722]/60 border-emerald-500/30 shadow-sm'
                            : 'bg-[#121722] border-[#1E2638] hover:border-[#3B82F6]/30'
                        }`}
                      >
                        <div className="p-3 flex items-center justify-between gap-3">
                          {/* Checkbox Button */}
                          <div className="flex items-center gap-3 min-w-0 flex-1">
                            <button
                              onClick={(e) => handleToggleHabit(habit.id, todayKey, e)}
                              className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 border transition-all active:scale-90 ${
                                isDoneToday
                                  ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400'
                                  : 'bg-[#0A0D14] border-[#1E2638] text-slate-600 hover:border-slate-600'
                              }`}
                            >
                              {isDoneToday ? (
                                <Check className="w-5 h-5 stroke-[3] text-emerald-400 animate-level-burst" />
                              ) : (
                                <span className="text-lg">{habit.icon}</span>
                              )}
                            </button>

                            <div className="min-w-0 flex-1">
                              <span
                                className={`font-bold text-sm block break-words ${
                                  isDoneToday ? 'line-through text-slate-500' : 'text-slate-100'
                                }`}
                              >
                                {habit.name}
                              </span>

                              <div className="flex items-center gap-2 mt-1 flex-wrap">
                                <span className="text-[10px] font-bold text-[#3B82F6] flex items-center gap-0.5">
                                  <Sparkles className="w-2.5 h-2.5" /> +{habit.xpReward} XP
                                </span>
                                <span className="text-[10px] font-semibold text-[#F5B041]">
                                  +{habit.goldReward}g
                                </span>
                                <span className="text-[9px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-[#0A0D14] border border-[#1E2638] text-slate-400">
                                  {habit.difficulty}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            {/* Edit Quest */}
                            <button
                              onClick={() => handleOpenEditQuest(habit)}
                              className="p-1.5 rounded-lg text-slate-500 hover:text-[#F5B041] hover:bg-[#F5B041]/10 transition"
                              title="Edit Quest"
                            >
                              <Pencil className="w-3.5 h-3.5" />
                            </button>

                            {/* Delete Quest */}
                            <button
                              onClick={() => handleDeleteQuest(habit.id, habit.name)}
                              className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-500/10 transition"
                              title="Delete Quest"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {/* -------------------------------------------------------- */}
          {/* TAB 2: LIVE FIRESTORE REAL-TIME LEADERBOARD              */}
          {/* -------------------------------------------------------- */}
          {activeTab === 'leaderboard' && (
            <div className="space-y-3.5">
              {/* Leaderboard Header with Refresh Button & Quota Cache Indicator */}
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <Trophy className="w-4 h-4 text-[#F5B041]" />
                  <h2 className="text-sm font-black uppercase tracking-wider text-slate-100">
                    Global Leaderboard
                  </h2>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded-full bg-[#121722] text-[#F5B041] border border-[#1E2638]" title="Cached for 5 minutes to prevent burning Firestore Spark quota">
                    5m Cache
                  </span>
                  <button
                    onClick={() => {
                      fetchLiveLeaderboard(true);
                      showToast('Leaderboard refreshed from Cloud Firestore.');
                    }}
                    disabled={leaderboardLoading}
                    className="p-1.5 rounded-lg bg-[#121722] border border-[#1E2638] text-slate-400 hover:text-white transition active:scale-95 disabled:opacity-50"
                    title="Manual refresh"
                  >
                    <RotateCw className={`w-3.5 h-3.5 ${leaderboardLoading ? 'animate-spin text-[#F5B041]' : ''}`} />
                  </button>
                </div>
              </div>

              {/* Clean Sorting Toggle: All-Time Rank vs Top Streaks */}
              <div className="grid grid-cols-2 gap-1 p-1 rounded-xl bg-[#121722] border border-[#1E2638]">
                <button
                  type="button"
                  onClick={() => setLeaderboardTab('all_time')}
                  className={`py-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    leaderboardTab === 'all_time'
                      ? 'bg-[#F5B041] text-[#0A0D14] shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Trophy className="w-3.5 h-3.5" />
                  <span>All-Time Rank</span>
                </button>
                <button
                  type="button"
                  onClick={() => setLeaderboardTab('streaks')}
                  className={`py-1.5 rounded-lg text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                    leaderboardTab === 'streaks'
                      ? 'bg-[#F5B041] text-[#0A0D14] shadow-sm'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Flame className="w-3.5 h-3.5 fill-current" />
                  <span>Top Streaks</span>
                </button>
              </div>

              {/* Pinned User Rank Card (Always pinned using already-loaded profile data: 0 extra reads) */}
              <div className="p-3 rounded-2xl bg-gradient-to-r from-[#121722] via-[#121722] to-[#121722] border-2 border-[#F5B041] flex items-center justify-between shadow-md shadow-[#F5B041]/10">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex flex-col items-center justify-center w-8 shrink-0">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Rank</span>
                    <span className="text-xs font-black text-[#F5B041]">#{userRank ?? 1}</span>
                  </div>
                  <div className="w-10 h-10 rounded-xl bg-[#0A0D14] flex items-center justify-center text-xl border border-[#F5B041] shrink-0">
                    {player.avatar}
                  </div>
                  <div className="min-w-0">
                    <div className="text-xs font-bold text-white flex items-center gap-1">
                      <span className="break-words leading-tight">{player.name || 'Your Hunter'}</span>
                      <span className="text-[10px] px-1 py-0.2 rounded bg-[#F5B041]/20 text-[#F5B041] font-black">
                        YOU
                      </span>
                      {player.isPro && <Crown className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />}
                    </div>
                    <div className="text-[10px] text-slate-400 font-medium">
                      Lv.{player.level} • {leaderboardTab === 'all_time' ? `${player.totalXP.toLocaleString()} XP` : `${player.streakDays}d streak`}
                    </div>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xs font-black text-[#F5B041]">
                    {leaderboardTab === 'all_time' ? `${player.totalXP.toLocaleString()} XP` : `🔥 ${player.streakDays}d`}
                  </span>
                </div>
              </div>

              {/* Loading Skeleton State */}
              {leaderboardLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <div
                      key={i}
                      className="p-3 rounded-2xl bg-[#121722] border border-[#1E2638] flex items-center justify-between animate-pulse"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-4 bg-[#1E2638] rounded" />
                        <div className="w-10 h-10 bg-[#1E2638] rounded-xl" />
                        <div className="space-y-1.5">
                          <div className="w-24 h-3 bg-[#1E2638] rounded" />
                          <div className="w-16 h-2.5 bg-[#1E2638] rounded" />
                        </div>
                      </div>
                      <div className="w-14 h-4 bg-[#1E2638] rounded" />
                    </div>
                  ))}
                </div>
              ) : leaderboardData.length === 0 ? (
                /* Empty State */
                <div className="py-12 px-6 rounded-2xl bg-[#121722] border border-[#1E2638] text-center">
                  <div className="w-12 h-12 rounded-2xl bg-[#0A0D14] border border-[#1E2638] flex items-center justify-center mx-auto mb-3 text-2xl text-[#F5B041]">
                    🏆
                  </div>
                  <h3 className="text-sm font-bold text-white">Be The First on the Leaderboard</h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-xs mx-auto">
                    Complete your daily habit quests to earn XP and claim the #1 Global Hunter rank!
                  </p>
                </div>
              ) : (
                /* Live Firestore Players List with Top-3 Podium Accents */
                <div className="space-y-2">
                  {leaderboardData.map((operative, idx) => {
                    const rankNum = idx + 1;
                    const isRank1 = rankNum === 1;
                    const isRank2 = rankNum === 2;
                    const isRank3 = rankNum === 3;
                    const isCurrentUser = operative.uid === currentUserId || (player.name && operative.username?.toLowerCase() === player.name?.toLowerCase());

                    // Podium border & background accents
                    let cardBorder = 'border-[#1E2638]';
                    let cardBg = 'bg-[#121722]';
                    let rankBadge = (
                      <span className="text-xs font-bold text-slate-500 w-6 text-center shrink-0">
                        #{rankNum}
                      </span>
                    );

                    if (isRank1) {
                      cardBorder = 'border-amber-400/50 shadow-md shadow-amber-500/10';
                      cardBg = 'bg-gradient-to-r from-amber-500/15 via-[#121722] to-[#121722]';
                      rankBadge = (
                        <div className="flex flex-col items-center justify-center w-6 shrink-0">
                          <Crown className="w-3.5 h-3.5 text-[#F5B041]" />
                          <span className="text-xs font-black text-[#F5B041]">#1</span>
                        </div>
                      );
                    } else if (isRank2) {
                      cardBorder = 'border-slate-300/40';
                      cardBg = 'bg-gradient-to-r from-slate-300/10 via-[#121722] to-[#121722]';
                      rankBadge = (
                        <div className="flex flex-col items-center justify-center w-6 shrink-0">
                          <Medal className="w-3.5 h-3.5 text-slate-300" />
                          <span className="text-xs font-black text-slate-300">#2</span>
                        </div>
                      );
                    } else if (isRank3) {
                      cardBorder = 'border-amber-700/40';
                      cardBg = 'bg-gradient-to-r from-amber-700/10 via-[#121722] to-[#121722]';
                      rankBadge = (
                        <div className="flex flex-col items-center justify-center w-6 shrink-0">
                          <Medal className="w-3.5 h-3.5 text-amber-600" />
                          <span className="text-xs font-black text-amber-500">#3</span>
                        </div>
                      );
                    }

                    return (
                      <div
                        key={operative.uid || idx}
                        className={`p-3 rounded-2xl border flex items-center justify-between transition-all ${cardBg} ${cardBorder}`}
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {rankBadge}
                          <div className="w-9 h-9 rounded-xl bg-[#0A0D14] flex items-center justify-center text-lg border border-[#1E2638] shrink-0">
                            {operative.avatar_id || '⚔️'}
                          </div>
                          <div className="min-w-0">
                            <div className="text-xs font-bold text-slate-100 flex items-center gap-1.5">
                              <span className="break-words leading-tight">{operative.username || 'Anonymous Hunter'}</span>
                              {isCurrentUser && (
                                <span className="text-[9px] px-1 rounded bg-[#F5B041]/20 text-[#F5B041] font-bold">
                                  You
                                </span>
                              )}
                              {operative.is_pro && (
                                <Crown className="w-3 h-3 text-[#F5B041] shrink-0" />
                              )}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Lv.{operative.level || 1}
                            </div>
                          </div>
                        </div>

                        <div className="text-right shrink-0">
                          <span className={`text-xs font-black ${isRank1 ? 'text-[#F5B041]' : isRank2 ? 'text-slate-300' : isRank3 ? 'text-amber-500' : 'text-slate-300'}`}>
                            {leaderboardTab === 'all_time'
                              ? `${(operative.total_xp || 0).toLocaleString()} XP`
                              : `🔥 ${operative.streak_days || 0}d`}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* -------------------------------------------------------- */}
          {/* TAB 3: REWARD SHOP                                       */}
          {/* -------------------------------------------------------- */}
          {activeTab === 'shop' && (
            <div className="space-y-3.5">
              {/* Treasury Header */}
              <div className="p-4 rounded-2xl bg-[#121722] border border-[#1E2638] flex items-center justify-between">
                <div>
                  <div className="text-[10px] font-bold text-[#F5B041] uppercase tracking-wider">Gold Vault</div>
                  <div className="text-2xl font-black text-white flex items-center gap-1.5 mt-0.5">
                    <span>🪙</span>
                    <span>{player.gold} Gold</span>
                  </div>
                </div>
                <button
                  onClick={() => setIsAddRewardModal(true)}
                  className="px-3 py-2 rounded-xl bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14] text-xs font-bold flex items-center gap-1 shadow-sm active:scale-95 transition"
                >
                  <Plus className="w-3.5 h-3.5 stroke-[3]" />
                  <span>Custom Loot</span>
                </button>
              </div>

              {/* Rewards List */}
              <div className="space-y-2">
                {rewards.map((reward) => {
                  const canAfford = player.gold >= reward.cost;

                  return (
                    <div
                      key={reward.id}
                      className="p-3 rounded-2xl bg-[#121722] border border-[#1E2638] flex items-center justify-between gap-3 shadow-sm"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 rounded-xl bg-[#0A0D14] border border-[#1E2638] flex items-center justify-center text-xl shrink-0">
                          {reward.icon}
                        </div>
                        <div className="min-w-0">
                          <div className="text-xs font-bold text-white break-words">{reward.name}</div>
                          <div className="text-[10px] text-slate-400 mt-0.5 flex items-center gap-2">
                            <span className="text-[#F5B041] font-bold">🪙 {reward.cost} Gold</span>
                            {reward.claimedCount > 0 && <span>• Claimed {reward.claimedCount}x</span>}
                          </div>
                        </div>
                      </div>

                      <button
                        onClick={() => handleClaimReward(reward)}
                        disabled={!canAfford}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold active:scale-95 transition shrink-0 ${
                          canAfford
                            ? 'bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14]'
                            : 'bg-[#0A0D14] text-slate-600 border border-[#1E2638] cursor-not-allowed'
                        }`}
                      >
                        Claim
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* -------------------------------------------------------- */}
          {/* TAB 4: PROFILE                                           */}
          {/* -------------------------------------------------------- */}
          {activeTab === 'profile' && (
            <div className="space-y-3.5">
              {/* Profile Screen Header with Settings Gear Button */}
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Hunter Dossier
                </span>
                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic('light');
                    setIsSettingsModal(true);
                  }}
                  className="px-2.5 py-1.5 rounded-xl bg-[#121722] hover:bg-[#1E2638] border border-[#1E2638] text-slate-300 hover:text-[#F5B041] transition active:scale-95 flex items-center gap-1.5 shadow-sm"
                  title="Settings & System Configuration"
                >
                  <Settings className="w-3.5 h-3.5" />
                  <span className="text-[11px] font-bold">Settings</span>
                </button>
              </div>

              {/* Profile Card */}
              <div className="p-4 rounded-2xl bg-[#121722] border border-[#1E2638] text-center shadow-sm">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-[#0A0D14] border-2 border-[#F5B041] flex items-center justify-center text-3xl shadow-md mb-2">
                  {player.avatar}
                </div>
                <h2 className="text-base font-black text-white break-words">{player.name}</h2>
                <div className="text-xs text-[#F5B041] font-bold mt-0.5">
                  Level {player.level} • {player.classTitle}
                </div>

                {/* Level / XP Progress Bar */}
                <div className="mt-3 px-2">
                  <div className="flex justify-between text-[10px] text-slate-400 font-medium mb-1">
                    <span>XP Progress</span>
                    <span>{player.currentXP} / {xpNeeded} XP ({xpPercentage}%)</span>
                  </div>
                  <div className="w-full h-2 bg-[#0A0D14] border border-[#1E2638] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-[#3B82F6] to-[#F5B041] rounded-full transition-all duration-300"
                      style={{ width: `${xpPercentage}%` }}
                    />
                  </div>
                </div>

                {/* Avatar Chooser */}
                <div className="mt-3.5 flex items-center justify-center gap-1.5">
                  {AVATAR_OPTIONS.map((av) => (
                    <button
                      key={av.title}
                      onClick={() => {
                        setPlayer((prev) => ({
                          ...prev,
                          avatar: av.icon,
                          classTitle: getPlayerTitle(prev.level, av.title)
                        }));
                        if (currentUserId && currentUserId !== 'user_init') {
                          updateDoc(doc(db, 'users', currentUserId), { avatar_id: av.icon }).catch(() => {});
                        }
                        triggerHaptic('light');
                        playCoinSound(!soundEnabled);
                        showToast(`Avatar updated: ${av.icon}`);
                      }}
                      className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm border transition ${
                        player.avatar === av.icon
                          ? 'bg-[#F5B041]/20 border-[#F5B041] scale-105'
                          : 'bg-[#0A0D14] border-[#1E2638] text-slate-400'
                      }`}
                    >
                      {av.icon}
                    </button>
                  ))}
                </div>
              </div>

              {/* 3 Clean Summary Stat Cards */}
              <div className="grid grid-cols-3 gap-2">
                <div className="p-3 rounded-2xl bg-[#121722] border border-[#1E2638] text-center shadow-sm">
                  <div className="text-base mb-1">🔥</div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Streak</div>
                  <div className="text-sm font-black text-[#F5B041] mt-0.5">{player.streakDays}d</div>
                </div>

                <div className="p-3 rounded-2xl bg-[#121722] border border-[#1E2638] text-center shadow-sm">
                  <div className="text-base mb-1">⚡</div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Quests</div>
                  <div className="text-sm font-black text-[#3B82F6] mt-0.5">{totalCompletedCount}</div>
                </div>

                <div className="p-3 rounded-2xl bg-[#121722] border border-[#1E2638] text-center shadow-sm">
                  <div className="text-base mb-1">🏆</div>
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">Rank</div>
                  <div className="text-sm font-black text-amber-300 mt-0.5">#{userRank ?? 1}</div>
                </div>
              </div>

              {/* Unlocked Badges Grid */}
              <div className="p-3.5 rounded-2xl bg-[#121722] border border-[#1E2638] shadow-sm">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-[#F5B041]" />
                    <span>Unlocked Badges ({(player.unlockedBadgeIds || []).length}/{BADGES_LIST.length})</span>
                  </h3>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {BADGES_LIST.map((b) => {
                    const isUnlocked = (player.unlockedBadgeIds || []).includes(b.id);
                    return (
                      <div
                        key={b.id}
                        className={`p-2.5 rounded-xl border flex items-start gap-2.5 transition ${
                          isUnlocked
                            ? 'bg-[#0A0D14] border-[#F5B041]/40'
                            : 'bg-[#0A0D14]/40 border-[#1E2638] opacity-50'
                        }`}
                      >
                        <div className="text-xl shrink-0 mt-0.5">{b.icon}</div>
                        <div className="min-w-0 flex-1">
                          <h4 className="text-xs font-bold text-slate-100 leading-snug break-words">
                            {b.name}
                          </h4>
                          <p className="text-[11px] text-slate-400 leading-tight break-words mt-0.5">
                            {b.reqText}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Level Up Pro (₹49/mo) Teaser Card (100% Free V1 Launch Ready) */}
              <div className="p-4 rounded-2xl bg-[#121722] border border-[#1E2638] space-y-3 shadow-sm">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Crown className="w-4 h-4 text-[#F5B041]" />
                    <span className="text-xs font-black tracking-wider text-white">LEVEL UP PRO</span>
                  </div>
                  <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[#F5B041]/10 text-[#F5B041] border border-[#F5B041]/20">
                    ₹49/mo • Coming Soon
                  </span>
                </div>

                <p className="text-[11px] text-slate-400">
                  Upgrade your productivity engine with VIP Hunter benefits:
                </p>

                <div className="space-y-1.5 text-xs text-slate-300">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />
                    <span>Unlimited Habits (Beyond 5 free slots)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />
                    <span>2x Monthly Streak Shields</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />
                    <span>Yearly Consistency Heatmap</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-[#F5B041] shrink-0" />
                    <span>Gold Leaderboard Nameplate</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleNotifyPro}
                  disabled={player.interestedInPro}
                  className={`w-full py-2.5 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-sm active:scale-95 ${
                    player.interestedInPro
                      ? 'bg-[#1E2638] text-slate-400 cursor-default'
                      : 'bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14]'
                  }`}
                >
                  <Bell className="w-3.5 h-3.5" />
                  <span>{player.interestedInPro ? '✓ Notification Request Registered' : 'Notify Me on Launch'}</span>
                </button>
              </div>

              {/* Sign Out Action */}
              <div className="pt-1">
                <button
                  onClick={handleSignOut}
                  className="w-full py-2 rounded-xl bg-[#121722] hover:bg-[#1E2638] border border-[#1E2638] text-xs font-semibold text-red-400 hover:text-red-300 transition flex items-center justify-center gap-1.5"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out of Hunter Account</span>
                </button>
              </div>
            </div>
          )}
        </main>

        {/* ======================================================== */}
        {/* CLEAN FLOATING + BUTTON IN BOTTOM-RIGHT (Quests Only)    */}
        {/* ======================================================== */}
        {activeTab === 'quests' && (
          <button
            onClick={() => setIsAddQuestModal(true)}
            className="fixed bottom-20 right-5 z-40 w-12 h-12 rounded-2xl bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14] flex items-center justify-center shadow-xl shadow-[#F5B041]/25 active:scale-95 transition-all"
            title="Add Habit Quest"
          >
            <Plus className="w-6 h-6 stroke-[3]" />
          </button>
        )}

        {/* ======================================================== */}
        {/* SIMPLIFIED BOTTOM NAVIGATION BAR (4 TABS ONLY)           */}
        {/* ======================================================== */}
        <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[#0A0D14]/95 backdrop-blur-xl border-t border-[#1E2638] py-2 px-3 flex justify-center">
          <div className="w-full max-w-md flex items-center justify-around">
            <button
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('quests');
              }}
              className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition active:scale-95 ${
                activeTab === 'quests' ? 'text-[#F5B041] font-bold' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <CheckCircle2 className="w-5 h-5" />
              <span className="text-[10px]">Quests</span>
            </button>

            <button
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('leaderboard');
              }}
              className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition active:scale-95 ${
                activeTab === 'leaderboard' ? 'text-[#F5B041] font-bold' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <Trophy className="w-5 h-5" />
              <span className="text-[10px]">Leaderboard</span>
            </button>

            <button
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('shop');
              }}
              className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition active:scale-95 ${
                activeTab === 'shop' ? 'text-[#F5B041] font-bold' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <ShoppingBag className="w-5 h-5" />
              <span className="text-[10px]">Shop</span>
            </button>

            <button
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('profile');
              }}
              className={`flex flex-col items-center gap-1 py-1 px-3 rounded-xl transition active:scale-95 ${
                activeTab === 'profile' ? 'text-[#F5B041] font-bold' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              <User className="w-5 h-5" />
              <span className="text-[10px]">Profile</span>
            </button>
          </div>
        </nav>
      </div>

      {/* ======================================================== */}
      {/* MODAL 1: ADD NEW QUEST                                   */}
      {/* ======================================================== */}
      {isAddQuestModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#121722] border border-[#1E2638] rounded-t-3xl sm:rounded-3xl max-w-md w-full p-5 shadow-2xl space-y-4 animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-[#F5B041]/20 border border-[#F5B041]/30 flex items-center justify-center text-[#F5B041]">
                  <Sword className="w-3.5 h-3.5" />
                </div>
                <h3 className="text-sm font-bold text-white">Create Daily Habit Quest</h3>
              </div>
              <button onClick={() => setIsAddQuestModal(false)} className="p-1 rounded-lg text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateQuest} className="space-y-3.5">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Quest Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Read 20 pages, 30m workout, meditate..."
                  value={newQuestName}
                  onChange={(e) => setNewQuestName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Quest Icon
                </label>
                <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
                  {EMOJI_BANK.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => setNewQuestIcon(emoji)}
                      className={`w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0 border transition ${
                        newQuestIcon === emoji
                          ? 'bg-[#F5B041]/20 border-[#F5B041] scale-105'
                          : 'bg-[#0A0D14] border-[#1E2638] hover:bg-[#1E2638]'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">
                    Difficulty & Rewards
                  </label>
                  <span className="text-[10px] text-slate-500">
                    {habits.length}/{MAX_FREE_HABITS} Slots Used
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {(['easy', 'medium', 'hard'] as Difficulty[]).map((diff) => {
                    const cfg = DIFFICULTY_MAP[diff];
                    return (
                      <button
                        key={diff}
                        type="button"
                        onClick={() => setNewQuestDifficulty(diff)}
                        className={`py-2 px-1 rounded-xl text-[10px] font-bold uppercase border flex flex-col items-center justify-center transition ${
                          newQuestDifficulty === diff
                            ? 'bg-[#F5B041] text-[#0A0D14] border-[#F5B041]'
                            : 'bg-[#0A0D14] border-[#1E2638] text-slate-400'
                        }`}
                      >
                        <span className="capitalize">{diff}</span>
                        <span className="text-[9px] opacity-80 mt-0.5">+{cfg.xp} XP • +{cfg.gold}g</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#1E2638]">
                <button
                  type="button"
                  onClick={() => setIsAddQuestModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider text-[#0A0D14] bg-[#F5B041] hover:bg-[#e5a031] transition shadow-sm"
                >
                  Enlist Quest
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: EDIT EXISTING QUEST                               */}
      {/* ======================================================== */}
      {editingHabit && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#121722] border border-[#1E2638] rounded-t-3xl sm:rounded-3xl max-w-md w-full p-5 shadow-2xl space-y-4 animate-in slide-in-from-bottom duration-200">
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-xl bg-[#3B82F6]/20 border border-[#3B82F6]/30 flex items-center justify-center text-[#3B82F6]">
                  <Pencil className="w-3.5 h-3.5" />
                </div>
                <h3 className="text-sm font-bold text-white">Edit Habit Quest</h3>
              </div>
              <button onClick={() => setEditingHabit(null)} className="p-1 rounded-lg text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdateQuest} className="space-y-3.5">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Quest Title
                </label>
                <input
                  type="text"
                  required
                  maxLength={100}
                  value={editQuestName}
                  onChange={(e) => setEditQuestName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                />
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Quest Icon
                </label>
                <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
                  {EMOJI_BANK.map((emoji) => (
                    <button
                      key={emoji}
                      type="button"
                      onClick={() => setEditQuestIcon(emoji)}
                      className={`w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0 border transition ${
                        editQuestIcon === emoji
                          ? 'bg-[#F5B041] border-[#F5B041] shadow-sm'
                          : 'bg-[#0A0D14] border-[#1E2638] hover:border-slate-600'
                      }`}
                    >
                      {emoji}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Difficulty & Rewards
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['easy', 'medium', 'hard'] as Difficulty[]).map((diff) => {
                    const cfg = DIFFICULTY_MAP[diff];
                    return (
                      <button
                        key={diff}
                        type="button"
                        onClick={() => setEditQuestDifficulty(diff)}
                        className={`py-2 px-1 rounded-xl text-[10px] font-bold uppercase border flex flex-col items-center justify-center transition ${
                          editQuestDifficulty === diff
                            ? 'bg-[#F5B041] text-[#0A0D14] border-[#F5B041]'
                            : 'bg-[#0A0D14] border-[#1E2638] text-slate-400'
                        }`}
                      >
                        <span className="capitalize">{diff}</span>
                        <span className="text-[9px] opacity-80 mt-0.5">+{cfg.xp} XP • +{cfg.gold}g</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#1E2638]">
                <button
                  type="button"
                  onClick={() => setEditingHabit(null)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider text-[#0A0D14] bg-[#F5B041] hover:bg-[#e5a031] transition shadow-sm"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 2: LEVEL UP CELEBRATION                            */}
      {/* ======================================================== */}
      {isLevelUpModal && levelUpData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-[#121722] border-2 border-[#F5B041] rounded-3xl max-w-sm w-full p-6 text-center shadow-2xl animate-level-burst">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-[#F5B041] text-[#0A0D14] flex items-center justify-center text-3xl shadow-lg mb-3 animate-bounce">
              👑
            </div>

            <div className="text-[11px] font-black tracking-widest uppercase text-[#F5B041]">SYSTEM NOTICE</div>
            <h2 className="text-2xl font-black text-white mt-0.5">
              LEVEL {levelUpData.newLevel} ACHIEVED
            </h2>

            <p className="text-xs font-bold text-slate-300 mt-1.5">
              Rank Title: <span className="text-[#F5B041]">"{levelUpData.title}"</span>
            </p>

            <div className="my-4 p-3 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-xs text-slate-300 space-y-1 text-left">
              <div className="text-[#F5B041] font-bold">✨ Level Milestone Rewards:</div>
              <div className="text-slate-400">• New Rank Title Unlocked</div>
              <div className="text-slate-400">• Global Leaderboard Rank Boosted 🏆</div>
            </div>

            <button
              onClick={() => setIsLevelUpModal(false)}
              className="w-full py-2.5 rounded-xl bg-[#F5B041] hover:bg-[#e5a031] text-[#0A0D14] font-black text-xs uppercase tracking-wider shadow-sm active:scale-95 transition"
            >
              Continue Journey
            </button>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 3: CUSTOM REWARD MODAL                             */}
      {/* ======================================================== */}
      {isAddRewardModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-[#121722] border border-[#1E2638] rounded-t-3xl sm:rounded-3xl max-w-md w-full p-5 shadow-2xl space-y-4 animate-in slide-in-from-bottom">
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-3">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <Gift className="w-4 h-4 text-[#F5B041]" />
                <span>Create Custom Real-Life Reward</span>
              </h3>
              <button onClick={() => setIsAddRewardModal(false)} className="p-1 rounded-lg text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddCustomReward} className="space-y-3.5">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                  Reward Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 1hr gaming, movie ticket, iced coffee..."
                  value={newRewardName}
                  onChange={(e) => setNewRewardName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                    Icon
                  </label>
                  <select
                    value={newRewardIcon}
                    onChange={(e) => setNewRewardIcon(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                  >
                    <option value="🎁">🎁 Gift</option>
                    <option value="🎮">🎮 Gaming</option>
                    <option value="🍕">🍕 Food</option>
                    <option value="🎬">🎬 Movie</option>
                    <option value="☕">☕ Coffee</option>
                    <option value="😴">😴 Nap</option>
                    <option value="🛍️">🛍️ Shopping</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                    Cost (Gold)
                  </label>
                  <input
                    type="number"
                    min={10}
                    max={1000}
                    value={newRewardCost}
                    onChange={(e) => setNewRewardCost(Number(e.target.value))}
                    className="w-full px-3 py-2.5 rounded-xl bg-[#0A0D14] border border-[#1E2638] text-white text-xs focus:outline-none focus:border-[#F5B041]"
                  />
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#1E2638]">
                <button
                  type="button"
                  onClick={() => setIsAddRewardModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl text-xs font-bold text-[#0A0D14] bg-[#F5B041] hover:bg-[#e5a031] transition"
                >
                  Add Loot to Shop
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 4: SETTINGS & COMPLIANCE BOTTOM SHEET             */}
      {/* ======================================================== */}
      {isSettingsModal && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-[#121722] border border-[#1E2638] rounded-t-3xl sm:rounded-3xl max-w-md w-full p-5 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto animate-in slide-in-from-bottom duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1E2638] pb-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-[#F5B041]/10 border border-[#F5B041]/30 flex items-center justify-center text-[#F5B041]">
                  <Settings className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">System Settings</h3>
                  <p className="text-[10px] text-slate-400">Audio, notifications, and compliance</p>
                </div>
              </div>
              <button
                onClick={() => setIsSettingsModal(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Section 1: Tactile & Audio Preferences */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                Audio & Alerts
              </span>

              {/* Sound Effects Toggle */}
              <div className="p-3 rounded-xl bg-[#0A0D14] border border-[#1E2638] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-slate-300">
                    {soundEnabled ? (
                      <Volume2 className="w-4 h-4 text-[#F5B041]" />
                    ) : (
                      <VolumeX className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200">Sound Effects</div>
                    <div className="text-[10px] text-slate-400">Audio chime on habit completion & level up</div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleToggleSound}
                  className={`w-11 h-6 rounded-full transition-colors relative flex items-center p-0.5 ${
                    soundEnabled ? 'bg-[#F5B041]' : 'bg-[#1E2638]'
                  }`}
                >
                  <span
                    className={`w-5 h-5 rounded-full bg-[#0A0D14] shadow-sm transform transition-transform ${
                      soundEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* 9:00 PM Streak Protection Reminder Toggle */}
              <div className="p-3 rounded-xl bg-[#0A0D14] border border-[#1E2638] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-slate-300">
                    {reminderEnabled ? (
                      <Bell className="w-4 h-4 text-[#3B82F6]" />
                    ) : (
                      <BellOff className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200">9:00 PM Streak Alert</div>
                    <div className="text-[10px] text-slate-400">Daily reminder if quests remain incomplete</div>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={handleToggleReminder}
                  className={`w-11 h-6 rounded-full transition-colors relative flex items-center p-0.5 ${
                    reminderEnabled ? 'bg-[#3B82F6]' : 'bg-[#1E2638]'
                  }`}
                >
                  <span
                    className={`w-5 h-5 rounded-full bg-[#0A0D14] shadow-sm transform transition-transform ${
                      reminderEnabled ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>

            {/* Section 2: Legal & Support (Play Store Compliance) */}
            <div className="space-y-2 pt-1">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1">
                Legal & Support
              </span>

              {/* Privacy Policy */}
              <a
                href={PRIVACY_POLICY_URL}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => triggerHaptic('light')}
                className="p-3 rounded-xl bg-[#0A0D14] hover:bg-[#161D2B] border border-[#1E2638] flex items-center justify-between transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-slate-300">
                    <FileText className="w-4 h-4 text-slate-400 group-hover:text-white" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-white">Privacy Policy</div>
                    <div className="text-[10px] text-slate-400">Data usage, encryption, and player privacy</div>
                  </div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300" />
              </a>

              {/* Terms of Service */}
              <a
                href={TERMS_OF_SERVICE_URL}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => triggerHaptic('light')}
                className="p-3 rounded-xl bg-[#0A0D14] hover:bg-[#161D2B] border border-[#1E2638] flex items-center justify-between transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-slate-300">
                    <FileText className="w-4 h-4 text-slate-400 group-hover:text-white" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-white">Terms of Service</div>
                    <div className="text-[10px] text-slate-400">Rules of engagement & terms of use</div>
                  </div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-300" />
              </a>

              {/* Beta Feedback */}
              <a
                href={FEEDBACK_URL}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => triggerHaptic('light')}
                className="p-3 rounded-xl bg-[#0A0D14] hover:bg-[#161D2B] border border-[#1E2638] hover:border-[#F5B041]/40 flex items-center justify-between transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#F5B041]/10 border border-[#F5B041]/30 flex items-center justify-center text-[#F5B041] text-sm">
                    💡
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-white">Give Beta Feedback</div>
                    <div className="text-[10px] text-slate-400">Share suggestions or report bugs</div>
                  </div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-slate-500 group-hover:text-[#F5B041]" />
              </a>

              {/* Developer Support Email */}
              <a
                href={`mailto:${SUPPORT_EMAIL}`}
                onClick={() => triggerHaptic('light')}
                className="p-3 rounded-xl bg-[#0A0D14] hover:bg-[#161D2B] border border-[#1E2638] flex items-center justify-between transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#121722] border border-[#1E2638] flex items-center justify-center text-slate-300">
                    <Mail className="w-4 h-4 text-slate-400 group-hover:text-white" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-200 group-hover:text-white">Support & Feedback</div>
                    <div className="text-[10px] text-slate-400">{SUPPORT_EMAIL}</div>
                  </div>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-slate-300" />
              </a>
            </div>

            {/* Version & Build */}
            <div className="text-center py-1">
              <span className="text-[10px] text-slate-500">
                LEVEL UP v{APP_VERSION} (Build {BUILD_NUMBER}) • Production RPG System
              </span>
            </div>

            {/* Section 3: Account Actions (Log Out & Mandatory Delete Account) */}
            <div className="pt-2 border-t border-[#1E2638] space-y-2">
              <button
                type="button"
                onClick={handleSignOut}
                className="w-full py-2.5 rounded-xl bg-[#0A0D14] hover:bg-[#1E2638] border border-[#1E2638] text-xs font-semibold text-slate-300 hover:text-white transition flex items-center justify-center gap-2"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out of Account</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  triggerHaptic('warning');
                  setIsDeleteAccountModal(true);
                }}
                className="w-full py-2.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-xs font-semibold text-red-400 hover:text-red-300 transition flex items-center justify-center gap-2"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Account & Purge Data</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL 5: MANDATORY ACCOUNT DELETION CONFIRMATION         */}
      {/* ======================================================== */}
      {isDeleteAccountModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in">
          <div className="bg-[#121722] border border-red-500/40 rounded-3xl max-w-sm w-full p-6 text-center shadow-2xl space-y-4 animate-in zoom-in-95 duration-200">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-400">
              <AlertCircle className="w-7 h-7" />
            </div>

            <div className="space-y-1">
              <h3 className="text-base font-black text-white">Delete Hunter Account?</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                This action is <strong className="text-red-400">permanent and irreversible</strong>. Your operative profile, level, earned XP, streak counters, quest log, and custom shop rewards will be permanently wiped from Cloud Firestore and Firebase Auth.
              </p>
            </div>

            <div className="pt-2 space-y-2">
              <button
                type="button"
                disabled={isDeletingAccount}
                onClick={handleDeleteAccountAndData}
                className="w-full py-3 rounded-xl bg-red-600 hover:bg-red-700 text-white font-black text-xs uppercase tracking-wider transition active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2 shadow-md shadow-red-600/30"
              >
                {isDeletingAccount ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    <span>Permanently Purge All Data</span>
                  </>
                )}
              </button>

              <button
                type="button"
                disabled={isDeletingAccount}
                onClick={() => setIsDeleteAccountModal(false)}
                className="w-full py-2.5 rounded-xl bg-[#0A0D14] hover:bg-[#1E2638] text-slate-300 text-xs font-bold transition"
              >
                Cancel & Return
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
