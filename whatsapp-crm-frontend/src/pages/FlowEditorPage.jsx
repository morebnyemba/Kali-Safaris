// src/pages/FlowEditorPage.jsx
import React, { useEffect, useCallback } from 'react';
import { useAtom } from 'jotai';
import { useParams, useNavigate, Link } from 'react-router-dom';

// Shadcn/ui and other imports
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel } from '@/components/ui/select';
import { Dialog, DialogTrigger, DialogClose, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Separator } from '@/components/ui/separator';
import { Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';

// Icons
import {
  FiSave, FiPlus, FiArrowLeft, FiSettings, FiGitBranch, FiLoader, FiAlertCircle, FiTrash2, FiChevronsRight, FiInfo
} from 'react-icons/fi';

// Notifications
import { toast } from 'sonner';

// Import your editor modals (ensure paths are correct)
import StepConfigEditor from '@/components/bot_builder/StepConfigEditor';
import TransitionEditorModal from '@/components/bot_builder/TransitionEditorModal';

// Import Jotai atoms
import {
  STEP_TYPE_CHOICES,
  flowDetailsAtom,
  stepsAtom,
  transitionsAtom,
  isLoadingFlowAtom,
  isSavingFlowAtom,
  isOperatingOnStepAtom,
  isLoadingTransitionsAtom,
  flowEditorErrorAtom,
  showAddStepModalAtom,
  newStepNameAtom,
  newStepTypeAtom,
  editingStepAtom,
  managingTransitionsForStepAtom,
  editingTransitionAtom,
} from '@/atoms/flowEditorAtoms';

import { flowsApi } from '@/lib/api';

// --- Main Component ---
export default function FlowEditorPage() {
  const { flowId: flowIdFromParams } = useParams();
  const navigate = useNavigate();
  const logger = console;

  // State managed by Jotai
  const [flowDetails, setFlowDetails] = useAtom(flowDetailsAtom);
  const [steps, setSteps] = useAtom(stepsAtom);
  const [stepTransitions, setStepTransitions] = useAtom(transitionsAtom);
  const [isLoading, setIsLoading] = useAtom(isLoadingFlowAtom);
  const [isSavingFlow, setIsSavingFlow] = useAtom(isSavingFlowAtom);
  const [isOperatingOnStep, setIsOperatingOnStep] = useAtom(isOperatingOnStepAtom);
  const [isLoadingTransitions, setIsLoadingTransitions] = useAtom(isLoadingTransitionsAtom);
  const [error, setError] = useAtom(flowEditorErrorAtom);
  const [showAddStepModal, setShowAddStepModal] = useAtom(showAddStepModalAtom);
  const [newStepName, setNewStepName] = useAtom(newStepNameAtom);
  const [newStepType, setNewStepType] = useAtom(newStepTypeAtom);
  
  const [editingStep, setEditingStep] = useAtom(editingStepAtom);
  const [managingTransitionsForStep, setManagingTransitionsForStep] = useAtom(managingTransitionsForStepAtom);
  const [editingTransition, setEditingTransition] = useAtom(editingTransitionAtom);

  // Fetch flow data
  useEffect(() => {
    const isNewFlow = !flowIdFromParams || flowIdFromParams === 'new';
    const initialFlowState = { id: null, name: 'New Untitled Flow', description: '', triggerKeywordsRaw: '', nlpIntent: '', isActive: true };
    setFlowDetails(isNewFlow ? initialFlowState : initialFlowState);
    setSteps([]);
    setStepTransitions([]);
    setEditingStep(null); setManagingTransitionsForStep(null); setEditingTransition(null);

    if (!isNewFlow) {
      setIsLoading(true);
      const loadFullFlowData = async () => {
        try {
          logger.info(`Loading flow data for ID: ${flowIdFromParams}`);
          const flowResponse = await flowsApi.retrieve(flowIdFromParams);
          const fetchedFlow = flowResponse.data;
          setFlowDetails({
            id: fetchedFlow.id, name: fetchedFlow.name || '', description: fetchedFlow.description || '',
            triggerKeywordsRaw: (fetchedFlow.trigger_keywords || []).join(', '),
            nlpIntent: fetchedFlow.nlp_trigger_intent || '',
            isActive: fetchedFlow.is_active !== undefined ? fetchedFlow.is_active : true,
          });
          const stepsResponse = await flowsApi.listSteps(flowIdFromParams);
          const fetchedSteps = stepsResponse.data;
          const getDisplayType = (stepType) => STEP_TYPE_CHOICES.find(c => c.value === stepType)?.label || stepType;
          setSteps((fetchedSteps.results || fetchedSteps || []).map(s => ({...s, step_type_display: getDisplayType(s.step_type)})));
          setError(null);
        } catch (err) { setError(err.message); setFlowDetails(prev => ({...prev, name: "Error Loading Flow Data"})); }
        finally { setIsLoading(false); }
      };
      loadFullFlowData();
    } else {
      logger.info("Initializing for new flow creation.");
      setIsLoading(false);
    }
  }, [flowIdFromParams, logger, setFlowDetails, setSteps, setStepTransitions, setEditingStep, setManagingTransitionsForStep, setEditingTransition, setIsLoading, setError]);

  const handleFlowDetailChange = (field, value) => setFlowDetails(prev => ({ ...prev, [field]: value }));

  const handleSaveFlowDetails = async () => {
    if (!flowDetails.name.trim()) { toast.error("Flow name is required."); return; }
    setIsSavingFlow(true); setError(null);
    const isNewFlowCreation = !flowDetails.id;
    const payload = {
      name: flowDetails.name, description: flowDetails.description, is_active: flowDetails.isActive,
      trigger_keywords: flowDetails.triggerKeywordsRaw.split(',').map(k => k.trim()).filter(k => k),
      nlp_trigger_intent: flowDetails.nlpIntent || null,
    };
    try {
      let savedFlowData;
      if (isNewFlowCreation) {
        const response = await flowsApi.create(payload);
        savedFlowData = response.data;
        toast.success(`Flow "${savedFlowData.name}" created successfully!`);
        setFlowDetails(prev => ({...prev, id: savedFlowData.id, ...savedFlowData}));
        navigate(`/flows/edit/${savedFlowData.id}`, { replace: true });
      } else {
        const response = await flowsApi.update(flowDetails.id, payload);
        savedFlowData = response.data;
        toast.success(`Flow "${savedFlowData.name}" details updated!`);
        setFlowDetails(prev => ({...prev, ...savedFlowData}));
      }
    } catch (err) { setError(err.message); }
    finally { setIsSavingFlow(false); }
  };

  const handleAddNewStep = async () => {
    if (!newStepName.trim() || !newStepType) { toast.error("Step name and type are required."); return; }
    if (!flowDetails.id) { toast.error("Save the Flow first before adding steps."); return; }
    setIsOperatingOnStep(true);
    let initialConfig = {};
    if (newStepType === 'send_message') initialConfig = { message_type: 'text', text: { body: '' } };
    else if (newStepType === 'question') initialConfig = { message_config: { message_type: 'text', text: { body: '' }}, reply_config: { save_to_variable: 'user_answer', expected_type: 'text'} };
    else if (newStepType === 'action') initialConfig = { actions_to_run: [] };
    else if (newStepType === 'start_flow_node') initialConfig = { note: "Flow Entry Point" };
    else if (newStepType === 'end_flow') initialConfig = { note: "Flow End Point" };
    else initialConfig = { }; // Default for condition, etc.

    const newStepPayload = {
      flow: flowDetails.id, name: newStepName, step_type: newStepType, config: initialConfig,
      is_entry_point: !steps.some(s => s.is_entry_point),
    };
    try {
      const response = await flowsApi.createStep(flowDetails.id, newStepPayload);
      const createdStep = response.data;
      const getDisplayType = (stepType) => STEP_TYPE_CHOICES.find(c => c.value === stepType)?.label || stepType;
      setSteps(prev => [...prev, {...createdStep, step_type_display: getDisplayType(createdStep.step_type)}]);
      toast.success(`Step "${createdStep.name}" added.`);
      setNewStepName(''); setNewStepType(STEP_TYPE_CHOICES[0]?.value); setShowAddStepModal(false);
    } catch (err) { logger.error("Error adding new step:", err.data || err.message); }
    finally { setIsOperatingOnStep(false); }
  };
  
  const handleOpenEditStepModal = (stepToEdit) => setEditingStep(stepToEdit);

  const handleSaveEditedStep = async (stepId, updatedStepDataFromModal) => {
    if (!flowDetails.id) { toast.error("Flow ID is missing."); return false; }
    // No need to set isOperatingOnStep here, StepConfigEditor has its own isSavingStep
    let success = false;
    try {
        const response = await flowsApi.patchStep(flowDetails.id, stepId, updatedStepDataFromModal);
        const patchedStep = response.data;
        const getDisplayType = (stepType) => STEP_TYPE_CHOICES.find(c => c.value === stepType)?.label || stepType;
        setSteps(prev => prev.map(step => step.id === patchedStep.id ? { ...step, ...patchedStep, step_type_display: getDisplayType(patchedStep.step_type) } : step));
        toast.success(`Step "${patchedStep.name}" updated.`);
        success = true;
    } catch (err) {
        if (err.data && typeof err.data === 'object') {
            Object.entries(err.data).forEach(([field, messages]) => {
                toast.error(`${field.replace(/_/g, " ")}: ${Array.isArray(messages) ? messages.join(', ') : messages}`);
            });
        } success = false;
    }
    return success;
  };

  const handleDeleteStep = async (stepId, stepName) => {
    if (!window.confirm(`Delete step "${stepName}" and its transitions?`)) return;
    if (!flowDetails.id) return;
    setIsOperatingOnStep(true);
    try {
      await flowsApi.deleteStep(flowDetails.id, stepId);
      setSteps(prev => prev.filter(step => step.id !== stepId));
      toast.success(`Step "${stepName}" deleted.`);
      if (editingStep?.id === stepId) setEditingStep(null);
      if (managingTransitionsForStep?.id === stepId) setManagingTransitionsForStep(null);
    } catch (err) { /* toast handled by apiCall */ }
    finally { setIsOperatingOnStep(false); }
  };

  const handleOpenManageTransitions = async (step) => {
    if (!flowDetails.id || !step?.id) { toast.error("Flow/Step info missing."); return; }
    setManagingTransitionsForStep(step); setEditingTransition(null); setIsLoadingTransitions(true);
    try {
      const response = await flowsApi.listTransitions(flowDetails.id, step.id);
      const fetchedTransitions = response.data;
      setStepTransitions(fetchedTransitions.results || fetchedTransitions || []);
    } catch (err) { setStepTransitions([]); }
    finally { setIsLoadingTransitions(false); }
  };

  const handleSaveTransition = async (isEditingMode, transitionIdToUpdate, transitionDataFromModal) => {
    if (!managingTransitionsForStep?.id || !flowDetails.id) { toast.error("Context missing for saving transition."); return false; }
    const currentStepId = managingTransitionsForStep.id;
    let success = false;
    try {
      let savedTransition;
      const payload = { ...transitionDataFromModal };
      if (!isEditingMode) payload.current_step = currentStepId;
      const response = isEditingMode
        ? await flowsApi.updateTransition(flowDetails.id, currentStepId, transitionIdToUpdate, payload)
        : await flowsApi.createTransition(flowDetails.id, currentStepId, payload);
      savedTransition = response.data;
      if (isEditingMode) {
        setStepTransitions(prev => prev.map(t => t.id === savedTransition.id ? savedTransition : t));
        toast.success("Transition updated!");
      } else {
        setStepTransitions(prev => [...prev, savedTransition]);
        toast.success("Transition added!");
      }
      success = true;
    } catch (err) {
      if (err.data && typeof err.data === 'object') {
          Object.entries(err.data).forEach(([field, messages]) => {
              toast.error(`${field.replace(/_/g, " ")}: ${Array.isArray(messages) ? messages.join(', ') : messages}`);
          });
      } success = false;
    }
    return success;
  };

  const handleDeleteTransition = async (transitionIdToDelete) => {
    if (!managingTransitionsForStep?.id || !flowDetails.id || !transitionIdToDelete) return;
    if (!window.confirm("Delete this transition?")) return;
    const currentStepId = managingTransitionsForStep.id;
    try {
      await flowsApi.deleteTransition(flowDetails.id, currentStepId, transitionIdToDelete);
      setStepTransitions(prev => prev.filter(t => t.id !== transitionIdToDelete));
      toast.success("Transition deleted.");
      if (editingTransition?.id === transitionIdToDelete) setEditingTransition(null);
    } catch (err) { /* toast handled */ }
  };

  // --- RENDER LOGIC ---
  if (isLoading) return <div className="flex items-center justify-center h-screen"><FiLoader className="animate-spin h-16 w-16 text-blue-600 dark:text-blue-300" /> <p className="ml-4 text-2xl dark:text-slate-300">Loading Flow Editor...</p></div>;
  if (error && !flowDetails.id && flowIdFromParams && flowIdFromParams !== 'new') {
    return (
      <div className="container mx-auto p-8 text-center">
        <Card className="max-w-md mx-auto border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/10">
          <CardContent className="p-8"><FiAlertCircle size={56} className="mx-auto mb-4 text-red-500 dark:text-red-600"/><h2 className="text-2xl font-semibold text-red-700 dark:text-red-400 mb-3">Error Loading Flow</h2><p className="mb-6 text-red-600 dark:text-red-500 text-sm">{error}</p><Button variant="outline" onClick={() => navigate('/flows')} className="dark:text-slate-300 dark:border-slate-600"><FiArrowLeft className="mr-2"/> Back to Flows List</Button></CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 md:p-6 space-y-6 mb-20">
      {/* Header */}
      <div className="flex flex-wrap justify-between items-center gap-4 pb-4 border-b dark:border-slate-700">
        <div className="flex items-center gap-3 flex-grow min-w-0">
            <TooltipProvider><Tooltip><TooltipTrigger asChild>
                <Button variant="outline" size="icon" onClick={() => navigate('/flows')} className="dark:text-slate-300 dark:border-slate-600 h-10 w-10 flex-shrink-0"><FiArrowLeft className="h-5 w-5" /></Button>
            </TooltipTrigger><TooltipContent><p>Back to Flows List</p></TooltipContent></Tooltip></TooltipProvider>
            <div className="flex-grow min-w-0">
                <Input id="flowPageName" value={flowDetails.name} onChange={(e) => handleFlowDetailChange('name', e.target.value)} className="text-xl sm:text-2xl md:text-3xl font-bold dark:text-slate-50 dark:bg-transparent border-0 border-b-2 border-transparent focus:border-blue-500 dark:focus:border-blue-400 focus:ring-0 h-auto p-0 truncate" placeholder="Flow Name"/>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">ID: {flowDetails.id || "Unsaved"}</p>
            </div>
        </div>
        <Button onClick={handleSaveFlowDetails} disabled={isSavingFlow || isLoading} className="bg-green-600 hover:bg-green-700 text-white dark:bg-green-500 dark:hover:bg-green-600 min-w-[140px] h-10 flex-shrink-0">
          {isSavingFlow ? <FiLoader className="animate-spin mr-2" /> : <FiSave className="mr-2 h-4 w-4" />}
          {isSavingFlow ? 'Saving...' : (flowDetails.id ? 'Save Flow Details' : 'Create & Save Flow')}
        </Button>
      </div>

      {/* Flow Metadata Card */}
      <Card className="dark:bg-slate-800 dark:border-slate-700">
        <CardHeader>
            <CardTitle className="dark:text-slate-100 text-lg flex items-center gap-2"><FiSettings/> Flow Configuration</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          <div className="md:col-span-2 space-y-1"><Label htmlFor="flowDesc" className="dark:text-slate-300">Description</Label><Textarea id="flowDesc" value={flowDetails.description} onChange={(e) => handleFlowDetailChange('description', e.target.value)} rows={2} className="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100" placeholder="A brief summary of what this flow achieves."/></div>
          <div className="space-y-1"><Label htmlFor="triggerKeywords" className="dark:text-slate-300">Trigger Keywords (comma-separated)</Label><Input id="triggerKeywords" value={flowDetails.triggerKeywordsRaw} onChange={(e) => handleFlowDetailChange('triggerKeywordsRaw', e.target.value)} className="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100" placeholder="e.g., hi, start, menu"/></div>
          <div className="space-y-1"><Label htmlFor="nlpIntent" className="dark:text-slate-300">NLP Trigger Intent (Optional)</Label><Input id="nlpIntent" value={flowDetails.nlpIntent} onChange={(e) => handleFlowDetailChange('nlpIntent', e.target.value)} className="dark:bg-slate-700 dark:border-slate-600 dark:text-slate-100" placeholder="e.g., UserRequestQuote"/></div>
          <div className="flex items-center space-x-2 md:col-span-2 pt-3">
            <Switch id="isActive" checked={flowDetails.isActive} onCheckedChange={(val) => handleFlowDetailChange('isActive', val)} className="data-[state=checked]:bg-green-500"/>
            <Label htmlFor="isActive" className="dark:text-slate-300 cursor-pointer">Flow is Active</Label>
            <TooltipProvider delayDuration={100}><Tooltip>
                <TooltipTrigger type="button" className="ml-1 text-slate-400 dark:text-slate-500"><FiInfo size={14}/></TooltipTrigger>
                <TooltipContent><p className="text-xs max-w-xs">Active flows can be triggered by users. Inactive flows are saved but not live.</p></TooltipContent>
            </Tooltip></TooltipProvider>
          </div>
        </CardContent>
      </Card>

      {/* Flow Steps Management Card */}
      {flowDetails.id && ( // Only show steps if flow is saved and has an ID
        <Card className="dark:bg-slate-800 dark:border-slate-700">
          <CardHeader className="flex flex-row items-center justify-between">
            <div><CardTitle className="dark:text-slate-100 text-lg">Flow Steps</CardTitle><CardDescription className="dark:text-slate-400">Define the sequence of messages, questions, and actions for this flow.</CardDescription></div>
            <Dialog open={showAddStepModal} onOpenChange={setShowAddStepModal}>
              <DialogTrigger asChild><Button variant="outline" className="dark:text-slate-300 dark:border-slate-600 dark:hover:bg-slate-700"><FiPlus className="mr-2 h-4 w-4" /> Add Step</Button></DialogTrigger>
              <DialogContent className="sm:max-w-md dark:bg-slate-800 dark:text-slate-50">
                <DialogHeader><DialogTitle>Add New Step to "{flowDetails.name}"</DialogTitle></DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-1"><Label htmlFor="newStepName" className="dark:text-slate-300">Step Name*</Label><Input id="newStepName" value={newStepName} onChange={(e) => setNewStepName(e.target.value)} className="dark:bg-slate-700 dark:border-slate-600"/></div>
                  <div className="space-y-1"><Label htmlFor="newStepType" className="dark:text-slate-300">Step Type*</Label>
                    <Select value={newStepType} onValueChange={setNewStepType}>
                      <SelectTrigger className="dark:bg-slate-700 dark:border-slate-600"><SelectValue placeholder="Select type" /></SelectTrigger>
                      <SelectContent className="dark:bg-slate-700 dark:text-slate-50">{STEP_TYPE_CHOICES.map(c => <SelectItem key={c.value} value={c.value} className="dark:hover:bg-slate-600 dark:focus:bg-slate-600">{c.label}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <DialogClose asChild><Button variant="outline" className="dark:text-slate-300 dark:border-slate-600">Cancel</Button></DialogClose>
                  <Button onClick={handleAddNewStep} disabled={isOperatingOnStep} className="bg-blue-600 hover:bg-blue-700 text-white">
                    {isOperatingOnStep ? <FiLoader className="animate-spin"/> : "Add Step"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardHeader>
          <CardContent>
            {steps.length === 0 ? <p className="text-slate-500 dark:text-slate-400 text-center py-6">This flow has no steps yet. Click "Add Step" to begin building the conversation path!</p> : (
              <div className="space-y-3">
                {/* TODO: Consider a drag-and-drop library for reordering steps visually */}
                {steps.map((step) => (
                  <Card key={step.id} className="dark:bg-slate-700/60 dark:border-slate-600/80 hover:shadow-md transition-shadow">
                    <CardHeader className="flex flex-col sm:flex-row justify-between sm:items-center p-3 gap-2">
                        <div className="flex-grow min-w-0">
                            <h4 className="font-medium dark:text-slate-100 truncate" title={step.name}>{step.name}</h4>
                            <p className="text-xs text-slate-400 dark:text-slate-400 flex items-center gap-2">
                                Type: {step.step_type_display || step.step_type} {/* Use step_type_display from reducer */}
                                {step.is_entry_point && <Badge variant="outline" className="border-green-400 text-green-500 dark:text-green-300 text-xs px-1.5 py-0.5 ml-2">Entry Point</Badge>}
                            </p>
                        </div>
                        <div className="space-x-1 flex-shrink-0 self-start sm:self-center mt-2 sm:mt-0">
                            <TooltipProvider delayDuration={200}>
                                <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" onClick={() => handleOpenEditStepModal(step)} className="h-8 w-8 dark:text-slate-300 dark:hover:bg-slate-600"><FiSettings className="h-4 w-4 text-blue-400" /></Button></TooltipTrigger><TooltipContent><p>Configure Step</p></TooltipContent></Tooltip>
                                <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" onClick={() => handleOpenManageTransitions(step)} className="h-8 w-8 dark:text-slate-300 dark:hover:bg-slate-600"><FiGitBranch className="h-4 w-4 text-purple-400" /></Button></TooltipTrigger><TooltipContent><p>Manage Transitions</p></TooltipContent></Tooltip>
                                <Tooltip><TooltipTrigger asChild><Button variant="ghost" size="icon" onClick={() => handleDeleteStep(step.id, step.name)} className="h-8 w-8 text-red-500 hover:text-red-700 dark:hover:bg-red-900/40"><FiTrash2 className="h-4 w-4" /></Button></TooltipTrigger><TooltipContent><p>Delete Step</p></TooltipContent></Tooltip>
                            </TooltipProvider>
                        </div>
                    </CardHeader>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modals are rendered here, controlled by their respective state variables */}
      {editingStep && (
        <StepConfigEditor
          key={`step-config-${editingStep.id}`} // Force re-mount on step change
          isOpen={!!editingStep}
          step={editingStep}
          onClose={() => setEditingStep(null)}
          onSaveStep={handleSaveEditedStep} // This function makes the API call
        />
      )}

      {managingTransitionsForStep && (
        <TransitionEditorModal
          key={`trans-manage-${managingTransitionsForStep.id}`} // Force re-mount
          isOpen={!!managingTransitionsForStep}
          currentStep={managingTransitionsForStep}
          // Pass steps from the current flow, excluding the current step itself.
          // Ensure flowDetails.id is valid and steps are loaded before filtering.
          allStepsInFlow={flowDetails.id ? steps.filter(s => s.flow === flowDetails.id && s.id !== managingTransitionsForStep.id) : []}
          existingTransitions={stepTransitions} // These are transitions for the currentStep
          editingTransitionState={[editingTransition, setEditingTransition]}
          onClose={() => {
            setManagingTransitionsForStep(null);
            setEditingTransition(null);
            setStepTransitions([]); // Clear when modal closes
          }}
          onSave={handleSaveTransition} // Expects (isEditing, transitionId, payload)
          onDelete={handleDeleteTransition} // Expects (transitionId)
          isLoadingExternally={isLoadingTransitions}
        />
      )}
    </div>
  );
}