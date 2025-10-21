import { atom } from 'jotai';
import { atomWithStorage } from 'jotai/utils';

// Keys for localStorage
const ACCESS_TOKEN_KEY = 'accessToken';
const REFRESH_TOKEN_KEY = 'refreshToken';
const USER_DATA_KEY = 'user';

// --- Core State Atoms ---
// These atoms automatically sync with localStorage.
export const accessTokenAtom = atomWithStorage(ACCESS_TOKEN_KEY, null);
export const refreshTokenAtom = atomWithStorage(REFRESH_TOKEN_KEY, null);
export const userAtom = atomWithStorage(USER_DATA_KEY, null);

// --- Derived State Atoms ---
// This atom derives its value from another atom. It is read-only.
export const isAuthenticatedAtom = atom((get) => !!get(accessTokenAtom));

// --- UI State Atoms ---
// This atom is for managing loading states within the auth flow.
export const isLoadingAuthAtom = atom(true);