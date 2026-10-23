import { initializeApp, getApps, getApp, FirebaseApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, Auth } from 'firebase/auth';
import {
  initializeFirestore,
  persistentLocalCache,
  persistentMultipleTabManager,
  getFirestore,
  Firestore
} from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || 'AIzaSyAANuOZe_vTM9Uk2rG8TF87r3vP_msKbzE',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || 'level-up-3f79a.firebaseapp.com',
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || 'level-up-3f79a',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || 'level-up-3f79a.firebasestorage.app',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '303219866607',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '1:303219866607:web:8343148a01f2670d4fd41a',
  measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || 'G-VS28H5CE6C'
};

export const isFirebaseConfigured = (): boolean => {
  return (
    Boolean(firebaseConfig.apiKey) &&
    Boolean(firebaseConfig.projectId) &&
    firebaseConfig.projectId === 'level-up-3f79a'
  );
};

// Initialize Firebase App singleton
export const app: FirebaseApp = !getApps().length
  ? initializeApp(firebaseConfig)
  : getApp();

// Initialize Auth
export const auth: Auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();

// Initialize Firestore with offline persistence safely (lazy for SSR)
let firestoreDb: Firestore | null = null;

export const getFirestoreDb = (): Firestore => {
  if (firestoreDb) return firestoreDb;
  if (typeof window !== 'undefined') {
    try {
      firestoreDb = initializeFirestore(app, {
        localCache: persistentLocalCache({
          tabManager: persistentMultipleTabManager()
        })
      });
    } catch {
      firestoreDb = getFirestore(app);
    }
  } else {
    try {
      firestoreDb = getFirestore(app);
    } catch {
      firestoreDb = {} as Firestore;
    }
  }
  return firestoreDb;
};

export const db: Firestore = new Proxy({} as Firestore, {
  get(_target, prop) {
    const instance = getFirestoreDb();
    const val = (instance as any)[prop];
    if (typeof val === 'function') {
      return val.bind(instance);
    }
    return val;
  }
});

export interface UserProfile {
  uid: string;
  username: string;
  username_lowercase: string;
  avatar_id: string;
  level: number;
  xp: number;
  total_xp: number;
  gold: number;
  streak_days: number;
  last_completed_date: string | null;
  is_pro: boolean;
  interested_in_pro: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface HabitDocument {
  id?: string;
  title: string;
  difficulty: 'easy' | 'medium' | 'hard';
  icon: string;
  completed_dates: string[];
  created_at: string;
}

export const DIFFICULTY_REWARDS = {
  easy: { xp: 15, gold: 5 },
  medium: { xp: 30, gold: 10 },
  hard: { xp: 50, gold: 20 }
} as const;

export const MAX_FREE_HABITS = 5;

export const calculateLevel = (totalXp: number): number => {
  return 1 + Math.floor(Math.max(0, totalXp) / 200);
};

export const getTodayKey = (): string => {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const getYesterdayKey = (): string => {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};
