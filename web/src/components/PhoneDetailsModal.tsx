import React from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Separator } from './ui/separator';
import { 
  Smartphone, 
  Activity, 
  Calendar, 
  Clock, 
  Cpu, 
  HardDrive, 
  Wifi,
  Monitor,
  Settings,
  Play,
  Pause,
  RotateCcw,
  Trash2
} from 'lucide-react';
import { Phone } from '../App';

interface PhoneDetailsModalProps {
  phone: Phone;
  onClose: () => void;
}

export function PhoneDetailsModal({ phone, onClose }: PhoneDetailsModalProps) {
  const formatTimeRemaining = (hours: number) => {
    if (hours <= 0) return 'Expired';
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  const getStatusColor = (status: Phone['status']) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'inactive': return 'text-yellow-400';
      case 'expired': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const specs = [
    { icon: <Cpu className="w-4 h-4" />, label: 'Processor', value: 'Snapdragon 888' },
    { icon: <HardDrive className="w-4 h-4" />, label: 'RAM', value: '8GB' },
    { icon: <Monitor className="w-4 h-4" />, label: 'Display', value: '1080x2400' },
    { icon: <HardDrive className="w-4 h-4" />, label: 'Storage', value: '128GB' },
    { icon: <Wifi className="w-4 h-4" />, label: 'Network', value: '5G Ready' },
    { icon: <Settings className="w-4 h-4" />, label: 'OS', value: phone.apiLevel }
  ];

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-gray-900 border-gray-700 max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center space-x-2">
            <Smartphone className="w-5 h-5 text-blue-400" />
            <span>{phone.name}</span>
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Virtual Android device details and controls
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Status Overview */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center justify-between">
                <span className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>Status Overview</span>
                </span>
                <Badge variant={phone.status === 'active' ? 'default' : 'destructive'}>
                  {phone.status}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {phone.status === 'active' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Time remaining</span>
                    <span className={getStatusColor(phone.status)}>
                      {formatTimeRemaining(phone.timeRemaining)}
                    </span>
                  </div>
                  <Progress 
                    value={(phone.timeRemaining / 24) * 100} 
                    className="h-3"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>0h</span>
                    <span>24h</span>
                  </div>
                </div>
              )}

              {phone.status === 'expired' && (
                <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 text-center">
                  <Clock className="w-8 h-8 text-red-400 mx-auto mb-2" />
                  <p className="text-red-400">Phone has expired</p>
                  <p className="text-gray-400 text-sm">Top up to reactivate</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Created</span>
                  <p className="text-white">{formatDate(phone.createdAt)}</p>
                </div>
                <div>
                  <span className="text-gray-400">Last Payment</span>
                  <p className="text-white">{formatDate(phone.lastPayment)}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Device Information */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Device Information</CardTitle>
              <CardDescription className="text-gray-400">
                Hardware specifications and configuration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <span className="text-gray-400 text-sm">Model</span>
                  <p className="text-white">{phone.model}</p>
                </div>
                <div className="space-y-2">
                  <span className="text-gray-400 text-sm">Android Version</span>
                  <p className="text-white">{phone.apiLevel}</p>
                </div>
              </div>

              <Separator className="bg-gray-700" />

              <div className="space-y-3">
                <h4 className="text-white text-sm">Technical Specifications</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {specs.map((spec, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-gray-900/50 rounded-lg">
                      <div className="text-gray-400">
                        {spec.icon}
                      </div>
                      <div className="flex-1">
                        <p className="text-gray-400 text-xs">{spec.label}</p>
                        <p className="text-white text-sm">{spec.value}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Control Panel */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Control Panel</CardTitle>
              <CardDescription className="text-gray-400">
                Manage your virtual device
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Button
                  variant="outline"
                  className="flex flex-col items-center space-y-2 h-auto py-4 border-gray-600 text-gray-300 hover:bg-gray-700"
                  disabled={phone.status === 'expired'}
                >
                  <Play className="w-5 h-5" />
                  <span className="text-xs">Start</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="flex flex-col items-center space-y-2 h-auto py-4 border-gray-600 text-gray-300 hover:bg-gray-700"
                  disabled={phone.status === 'expired'}
                >
                  <Pause className="w-5 h-5" />
                  <span className="text-xs">Pause</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="flex flex-col items-center space-y-2 h-auto py-4 border-gray-600 text-gray-300 hover:bg-gray-700"
                  disabled={phone.status === 'expired'}
                >
                  <RotateCcw className="w-5 h-5" />
                  <span className="text-xs">Restart</span>
                </Button>
                
                <Button
                  variant="outline"
                  className="flex flex-col items-center space-y-2 h-auto py-4 border-red-600 text-red-400 hover:bg-red-900/20"
                >
                  <Trash2 className="w-5 h-5" />
                  <span className="text-xs">Delete</span>
                </Button>
              </div>

              {phone.status === 'active' && (
                <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
                  <div className="flex items-center space-x-2 text-green-400 text-sm">
                    <Activity className="w-4 h-4" />
                    <span>Phone is running and ready to use</span>
                  </div>
                  <p className="text-gray-400 text-xs mt-2">
                    Connect via web interface or ADB to start using your virtual device
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Usage Statistics */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Usage Statistics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div className="space-y-1">
                  <p className="text-gray-400 text-sm">Total Usage</p>
                  <p className="text-white text-lg">156h</p>
                </div>
                <div className="space-y-1">
                  <p className="text-gray-400 text-sm">Sessions</p>
                  <p className="text-white text-lg">23</p>
                </div>
                <div className="space-y-1">
                  <p className="text-gray-400 text-sm">Cost</p>
                  <p className="text-white text-lg">6.5 USDT</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex space-x-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
            >
              Close
            </Button>
            {phone.status !== 'active' && (
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                Top Up Phone
              </Button>
            )}
            {phone.status === 'active' && (
              <Button
                className="flex-1 bg-green-600 hover:bg-green-700"
              >
                Connect to Phone
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}