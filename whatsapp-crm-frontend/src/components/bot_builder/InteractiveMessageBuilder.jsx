import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { FiPlus, FiTrash2, FiInfo } from 'react-icons/fi';
import { Tooltip, TooltipProvider, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';

const ButtonActionEditor = ({ action, onActionChange }) => {
    const buttons = action?.buttons || [];

    const handleAddButton = () => {
        if (buttons.length >= 3) return;
        const newButton = { type: 'reply', reply: { id: `btn_${Date.now()}`, title: 'New Button' } };
        onActionChange({ buttons: [...buttons, newButton] });
    };

    const handleButtonChange = (index, field, value) => {
        const updatedButtons = buttons.map((btn, i) => 
            i === index ? { ...btn, reply: { ...btn.reply, [field]: value } } : btn
        );
        onActionChange({ buttons: updatedButtons });
    };

    const handleRemoveButton = (index) => {
        onActionChange({ buttons: buttons.filter((_, i) => i !== index) });
    };

    return (
        <div className="space-y-3">
            <Label>Buttons (Max 3)</Label>
            {buttons.map((button, index) => (
                <div key={index} className="flex items-center gap-2 p-2 border rounded-md">
                    <div className="flex-1 grid grid-cols-2 gap-2">
                        <Input 
                            placeholder="Button Title (max 20 chars)" 
                            value={button.reply.title}
                            maxLength="20"
                            onChange={(e) => handleButtonChange(index, 'title', e.target.value)}
                        />
                        <Input 
                            placeholder="Button ID (for transitions)" 
                            value={button.reply.id}
                            maxLength="256"
                            onChange={(e) => handleButtonChange(index, 'id', e.target.value)}
                        />
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => handleRemoveButton(index)} className="text-destructive">
                        <FiTrash2 className="h-4 w-4" />
                    </Button>
                </div>
            ))}
            {buttons.length < 3 && (
                <Button variant="outline" size="sm" onClick={handleAddButton}><FiPlus className="mr-2 h-4 w-4" /> Add Button</Button>
            )}
        </div>
    );
};

const ListActionEditor = ({ action, onActionChange }) => {
    const sections = action?.sections || [{ title: 'Section 1', rows: [{ id: `row_${Date.now()}`, title: 'Row 1', description: '' }] }];

    const handleSectionChange = (secIndex, field, value) => {
        const updatedSections = sections.map((sec, i) => i === secIndex ? { ...sec, [field]: value } : sec);
        onActionChange({ ...action, sections: updatedSections });
    };

    const handleRowChange = (secIndex, rowIndex, field, value) => {
        const updatedSections = [...sections];
        updatedSections[secIndex].rows[rowIndex] = { ...updatedSections[secIndex].rows[rowIndex], [field]: value };
        onActionChange({ ...action, sections: updatedSections });
    };

    const handleAddRow = (secIndex) => {
        const updatedSections = [...sections];
        if (updatedSections[secIndex].rows.length >= 10) return;
        updatedSections[secIndex].rows.push({ id: `row_${Date.now()}`, title: 'New Row', description: '' });
        onActionChange({ ...action, sections: updatedSections });
    };

    const handleRemoveRow = (secIndex, rowIndex) => {
        const updatedSections = [...sections];
        updatedSections[secIndex].rows = updatedSections[secIndex].rows.filter((_, i) => i !== rowIndex);
        onActionChange({ ...action, sections: updatedSections });
    };

    return (
        <div className="space-y-4">
            <div>
                <Label>List Button Text</Label>
                <Input 
                    placeholder="e.g., View Options" 
                    value={action?.button || ''}
                    maxLength="20"
                    onChange={(e) => onActionChange({ ...action, button: e.target.value })}
                />
            </div>
            <Label>List Sections</Label>
            {sections.map((section, secIndex) => (
                <Card key={secIndex} className="bg-background/50">
                    <CardHeader className="p-3">
                        <Input 
                            placeholder="Section Title (optional, max 24 chars)" 
                            value={section.title}
                            maxLength="24"
                            onChange={(e) => handleSectionChange(secIndex, 'title', e.target.value)}
                        />
                    </CardHeader>
                    <CardContent className="p-3 space-y-2">
                        <Label className="text-xs">Rows (Max 10 per section)</Label>
                        {section.rows.map((row, rowIndex) => (
                            <div key={rowIndex} className="flex items-center gap-2 p-2 border rounded-md">
                                <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2">
                                    <Input placeholder="Row Title (max 24)" value={row.title} maxLength="24" onChange={(e) => handleRowChange(secIndex, rowIndex, 'title', e.target.value)} />
                                    <Input placeholder="Row ID (for transitions)" value={row.id} maxLength="200" onChange={(e) => handleRowChange(secIndex, rowIndex, 'id', e.target.value)} />
                                    <Input placeholder="Description (optional, max 72)" value={row.description} maxLength="72" onChange={(e) => handleRowChange(secIndex, rowIndex, 'description', e.target.value)} />
                                </div>
                                <Button variant="ghost" size="icon" onClick={() => handleRemoveRow(secIndex, rowIndex)} className="text-destructive"><FiTrash2 className="h-4 w-4" /></Button>
                            </div>
                        ))}
                        {section.rows.length < 10 && (
                            <Button variant="outline" size="sm" onClick={() => handleAddRow(secIndex)}><FiPlus className="mr-2 h-4 w-4" /> Add Row</Button>
                        )}
                    </CardContent>
                </Card>
            ))}
            {/* For simplicity, adding new sections is omitted. Can be added with a similar pattern. */}
        </div>
    );
};

export default function InteractiveMessageBuilder({ value, onChange }) {
    const handleFieldChange = (field, fieldValue) => {
        onChange({ ...value, [field]: fieldValue });
    };

    const handleActionChange = (actionPayload) => {
        onChange({ ...value, action: { ...value.action, ...actionPayload } });
    };

    const handleInteractiveTypeChange = (newType) => {
        const newAction = newType === 'button' 
            ? { buttons: [{ type: 'reply', reply: { id: 'btn_1', title: 'Button 1' } }] }
            : { button: 'View Options', sections: [{ title: 'Section 1', rows: [{ id: 'row_1', title: 'Row 1' }] }] };
        onChange({ ...value, type: newType, action: newAction });
    };

    const handleHeaderTypeChange = (headerType) => {
        const newHeader = headerType === 'none' ? null : { type: headerType, text: '' };
        onChange({ ...value, header: newHeader });
    };

    const handleHeaderContentChange = (text) => {
        onChange({ ...value, header: { ...value.header, text } });
    };

    return (
        <div className="space-y-4 p-1">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <Label>Interactive Type</Label>
                    <Select value={value?.type || 'button'} onValueChange={handleInteractiveTypeChange}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="button">Button Reply</SelectItem>
                            <SelectItem value="list">List Message</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
                <div>
                    <Label>Header (Optional)</Label>
                    <Select value={value?.header?.type || 'none'} onValueChange={handleHeaderTypeChange}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                            <SelectItem value="none">None</SelectItem>
                            <SelectItem value="text">Text</SelectItem>
                            <SelectItem value="image" disabled>Image (soon)</SelectItem>
                            <SelectItem value="video" disabled>Video (soon)</SelectItem>
                            <SelectItem value="document" disabled>Document (soon)</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {value?.header?.type === 'text' && (
                <div>
                    <Label>Header Text (max 60 chars)</Label>
                    <Input 
                        value={value.header.text || ''}
                        maxLength="60"
                        onChange={(e) => handleHeaderContentChange(e.target.value)}
                    />
                </div>
            )}

            <div>
                <Label>Body Text (max 1024 chars)</Label>
                <Textarea 
                    placeholder="The main content of your message."
                    value={value?.body?.text || ''}
                    maxLength="1024"
                    onChange={(e) => handleFieldChange('body', { text: e.target.value })}
                    rows={3}
                />
            </div>

            <div>
                <Label>Footer Text (Optional, max 60 chars)</Label>
                <Input 
                    placeholder="Small text at the bottom."
                    value={value?.footer?.text || ''}
                    maxLength="60"
                    onChange={(e) => handleFieldChange('footer', { text: e.target.value })}
                />
            </div>

            <Card>
                <CardHeader className="p-3">
                    <CardTitle className="text-base flex items-center">
                        Action
                        <TooltipProvider><Tooltip><TooltipTrigger type="button" className="ml-2"><FiInfo size={14} /></TooltipTrigger><TooltipContent><p className="max-w-xs text-xs">Define the buttons or list options the user will see.</p></TooltipContent></Tooltip></TooltipProvider>
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                    {value?.type === 'button' && <ButtonActionEditor action={value.action} onActionChange={handleActionChange} />}
                    {value?.type === 'list' && <ListActionEditor action={value.action} onActionChange={handleActionChange} />}
                </CardContent>
            </Card>
        </div>
    );
}