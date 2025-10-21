import { atom } from 'jotai';

export const STEP_TYPE_CHOICES = [
    { value: 'send_message', label: 'Send Message' }, 
    { value: 'question', label: 'Ask Question' },
    { value: 'action', label: 'Perform Action' }, 
    { value: 'start_flow_node', label: 'Start Node (Entry)' },
    { value: 'end_flow', label: 'End Flow' }, 
    { value: 'condition', label: 'Condition Node (Visual)' },
    { value: 'human_handover', label: 'Handover to Human' },
    { value: 'switch_flow', label: 'Switch to Another Flow' },
];

const initialFlowDetailsState = {
  id: null, name: 'New Untitled Flow', description: '',
  triggerKeywordsRaw: '', nlpIntent: '', isActive: true,
};

// --- Core Data Atoms ---
export const flowDetailsAtom = atom(initialFlowDetailsState);
export const stepsAtom = atom([]);
export const transitionsAtom = atom([]);

// --- UI State Atoms ---
export const isLoadingFlowAtom = atom(true);
export const isSavingFlowAtom = atom(false);
export const isOperatingOnStepAtom = atom(false);
export const isLoadingTransitionsAtom = atom(false);
export const flowEditorErrorAtom = atom(null);

// --- Modal/Editing State Atoms ---
export const showAddStepModalAtom = atom(false);
export const newStepNameAtom = atom('');
export const newStepTypeAtom = atom(STEP_TYPE_CHOICES[0]?.value || 'send_message');

export const editingStepAtom = atom(null); // Will hold the step object being edited
export const managingTransitionsForStepAtom = atom(null); // Will hold the step object for transition management
export const editingTransitionAtom = atom(null); // Will hold the transition object being edited