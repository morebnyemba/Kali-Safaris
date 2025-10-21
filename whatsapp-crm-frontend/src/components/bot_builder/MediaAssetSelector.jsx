// src/components/bot_builder/MediaAssetSelector.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue, SelectGroup, SelectLabel
} from '@/components/ui/select';
import { toast } from 'sonner';
import { FiLoader, FiImage, FiFileText, FiVideo, FiMic,FiPaperclip } from 'react-icons/fi'; // Added more icons
import { mediaAssetsApi } from '@/lib/api';


const mediaTypeIcons = {
    image: <FiImage className="mr-2 h-4 w-4 text-blue-500" />,
    document: <FiFileText className="mr-2 h-4 w-4 text-green-500" />,
    video: <FiVideo className="mr-2 h-4 w-4 text-purple-500" />,
    audio: <FiMic className="mr-2 h-4 w-4 text-orange-500" />,
    default: <FiPaperclip className="mr-2 h-4 w-4" />
};

export default function MediaAssetSelector({ currentAssetPk, mediaTypeFilter, onAssetSelect, disabled = false }) {
  const [assets, setAssets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  // Consider a state to control dialog visibility if using a modal for selection
  // const [showAssetListDialog, setShowAssetListDialog] = useState(false);


  const fetchAssets = useCallback(async () => {
    if (!mediaTypeFilter) {
        toast.error("Media type filter is required to fetch assets.");
        return;
    }
    setIsLoading(true);
    try {
      const response = await mediaAssetsApi.list({ status: 'synced', media_type: mediaTypeFilter });
      const data = response.data;
      setAssets(data.results || data || []); // Handle paginated or direct list
    } catch (error) {
      // Error is toasted by apiCall, but local state can also be set
      setAssets([]);
    } finally {
      setIsLoading(false);
    }
  }, [mediaTypeFilter]);

  // Fetch assets when the component mounts or filter changes
  useEffect(() => {
    fetchAssets();
  }, [fetchAssets]);


  const selectedAssetDetails = assets.find(asset => asset.pk === currentAssetPk);

  return (
    <div className="space-y-2">
      <Select
        onValueChange={(pk) => onAssetSelect(pk ? parseInt(pk, 10) : null)}
        value={currentAssetPk?.toString() || ""}
        disabled={disabled || isLoading}
      >
        <SelectTrigger className="w-full dark:bg-slate-700 dark:border-slate-600">
          <SelectValue placeholder={isLoading ? "Loading assets..." : `Select a ${mediaTypeFilter}...`} />
        </SelectTrigger>
        <SelectContent className="dark:bg-slate-700 dark:text-slate-50">
          <SelectGroup>
            <SelectLabel className="dark:text-slate-400">
                Synced {mediaTypeFilter.charAt(0).toUpperCase() + mediaTypeFilter.slice(1)} Assets
            </SelectLabel>
            <SelectItem value="" className="dark:hover:bg-slate-600 dark:focus:bg-slate-600 italic">
                Clear Selection (None)
            </SelectItem>
            {isLoading && <div className="p-2 text-center text-xs"><FiLoader className="inline animate-spin mr-1" />Loading...</div>}
            {!isLoading && assets.length === 0 && (
              <div className="p-2 text-center text-xs text-slate-500 dark:text-slate-400">
                No synced {mediaTypeFilter} assets found.
              </div>
            )}
            {assets.map(asset => (
              <SelectItem key={asset.pk} value={asset.pk.toString()} className="dark:hover:bg-slate-600 dark:focus:bg-slate-600">
                <div className="flex items-center">
                    {mediaTypeIcons[asset.media_type] || mediaTypeIcons.default}
                    {asset.name}
                </div>
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
      {selectedAssetDetails && (
        <div className="text-xs p-2 border dark:border-slate-600 rounded-md bg-slate-50 dark:bg-slate-700/50">
            <p className="font-medium dark:text-slate-200">Selected: {selectedAssetDetails.name}</p>
            <p className="text-slate-500 dark:text-slate-400">WA ID: {selectedAssetDetails.whatsapp_media_id || "Not Synced"}</p>
        </div>
      )}
    </div>
  );
}