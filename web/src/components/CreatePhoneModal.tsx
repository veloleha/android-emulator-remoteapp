import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Smartphone, Cpu, Settings, Zap } from 'lucide-react';

interface CreatePhoneModalProps {
  onClose: () => void;
  onCreate: (phoneData: { name: string; model: string; apiLevel: string }) => void;
}

export function CreatePhoneModal({ onClose, onCreate }: CreatePhoneModalProps) {
  const [name, setName] = useState('');
  const [model, setModel] = useState('');
  const [apiLevel, setApiLevel] = useState('');

  const deviceModels = [
    { value: 'pixel-6', label: 'Google Pixel 6', specs: '8GB RAM, Snapdragon 888' },
    { value: 'pixel-7', label: 'Google Pixel 7', specs: '8GB RAM, Tensor G2' },
    { value: 'samsung-s21', label: 'Samsung Galaxy S21', specs: '8GB RAM, Exynos 2100' },
    { value: 'samsung-s22', label: 'Samsung Galaxy S22', specs: '8GB RAM, Snapdragon 8 Gen 1' },
    { value: 'oneplus-9', label: 'OnePlus 9', specs: '8GB RAM, Snapdragon 888' },
    { value: 'xiaomi-12', label: 'Xiaomi 12', specs: '8GB RAM, Snapdragon 8 Gen 1' }
  ];

  const apiLevels = [
    { value: 'api-29', label: 'API 29 (Android 10)', popular: false },
    { value: 'api-30', label: 'API 30 (Android 11)', popular: false },
    { value: 'api-31', label: 'API 31 (Android 12)', popular: true },
    { value: 'api-32', label: 'API 32 (Android 12L)', popular: false },
    { value: 'api-33', label: 'API 33 (Android 13)', popular: true },
    { value: 'api-34', label: 'API 34 (Android 14)', popular: true }
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (name && model && apiLevel) {
      const selectedModel = deviceModels.find(d => d.value === model);
      const selectedApi = apiLevels.find(a => a.value === apiLevel);
      
      onCreate({
        name,
        model: selectedModel?.label || model,
        apiLevel: selectedApi?.label || apiLevel
      });
    }
  };

  const isValid = name && model && apiLevel;

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center space-x-2">
            <Smartphone className="w-5 h-5 text-blue-400" />
            <span>Create New Phone</span>
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Configure your virtual Android device
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Phone Name */}
          <div className="space-y-2">
            <Label htmlFor="name" className="text-gray-300">Phone Name</Label>
            <Input
              id="name"
              placeholder="e.g., My Testing Phone"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-gray-800 border-gray-600 text-white placeholder-gray-500"
              required
            />
            <p className="text-xs text-gray-500">Give your phone a memorable name</p>
          </div>

          {/* Device Model */}
          <div className="space-y-3">
            <Label className="text-gray-300 flex items-center space-x-2">
              <Cpu className="w-4 h-4" />
              <span>Device Model</span>
            </Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {deviceModels.map((device) => (
                <Card 
                  key={device.value}
                  className={`cursor-pointer transition-all ${
                    model === device.value
                      ? 'bg-blue-600/20 border-blue-500' 
                      : 'bg-gray-800 border-gray-700 hover:bg-gray-800/70'
                  }`}
                  onClick={() => setModel(device.value)}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-white">{device.label}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-xs text-gray-400">
                      {device.specs}
                    </CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          {/* API Level */}
          <div className="space-y-3">
            <Label className="text-gray-300 flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Android API Level</span>
            </Label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {apiLevels.map((api) => (
                <Card 
                  key={api.value}
                  className={`cursor-pointer transition-all ${
                    apiLevel === api.value
                      ? 'bg-blue-600/20 border-blue-500' 
                      : 'bg-gray-800 border-gray-700 hover:bg-gray-800/70'
                  }`}
                  onClick={() => setApiLevel(api.value)}
                >
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm text-white flex items-center justify-between">
                      <span>{api.label}</span>
                      {api.popular && (
                        <span className="bg-green-500 text-white text-xs px-2 py-1 rounded">
                          Popular
                        </span>
                      )}
                    </CardTitle>
                  </CardHeader>
                </Card>
              ))}
            </div>
          </div>

          {/* Pricing Info */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Zap className="w-5 h-5 text-green-400" />
                  <div>
                    <p className="text-white">Instant Activation</p>
                    <p className="text-gray-400 text-sm">Your phone will be ready in seconds</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-green-400 text-lg">1 USDT</p>
                  <p className="text-gray-400 text-sm">per day</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!isValid}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Create Phone
            </Button>
          </div>
        </form>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Phone will start with 24 hours of usage time
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}