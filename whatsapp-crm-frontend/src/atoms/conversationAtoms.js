import { atom } from 'jotai';

// This atom will hold the currently selected contact object, or null.
// Any component in the app can now read or write to this state.
export const selectedContactAtom = atom(null);