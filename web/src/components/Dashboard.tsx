import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Avatar, AvatarFallback } from './ui/avatar';
import { 
  User, 
  Smartphone, 
  CreditCard, 
  LogOut, 
  Plus, 
  Clock, 
  DollarSign,
  Activity,
  Server,
  Zap,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { User as UserType, Phone } from '../App';

interface DashboardProps {
  user: UserType;
  phones: Phone[];
  onCreatePhone: () => void;
  onTopUp: (phoneId: string) => void;
  onPhoneDetails: (phone: Phone) => void;
  onLogout: () => void;
}

export function Dashboard({ user, phones, onCreatePhone, onTopUp, onPhoneDetails, onLogout }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<'phones' | 'profile' | 'payments'>('phones');

  const formatTimeRemaining = (hours: number) => {
    if (hours <= 0) return 'Expired';
    const h = Math.floor(hours);
    const m = Math.floor((hours - h) * 60);
    return `${h}h ${m}m`;
  };

  const getStatusColor = (status: Phone['status']) => {
    switch (status) {
      case 'active': return 'bg-green-500';
      case 'inactive': return 'bg-yellow-500';
      case 'expired': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: Phone['status']) => {
    switch (status) {
      case 'active': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'inactive': return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'expired': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return null;
    }
  };

  const activePhones = phones.filter(p => p.status === 'active').length;
  const expiredPhones = phones.filter(p => p.status === 'expired').length;

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
              <Smartphone className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-white">Emulator Hub</h2>
              <p className="text-gray-400 text-sm">@{user.telegramUsername}</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <button
            onClick={() => setActiveTab('phones')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'phones' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <Smartphone className="w-5 h-5" />
            <span>My Phones</span>
            <Badge variant="secondary" className="ml-auto bg-gray-700 text-gray-300">
              {phones.length}
            </Badge>
          </button>

          <button
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'profile' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <User className="w-5 h-5" />
            <span>Profile</span>
          </button>

          <button
            onClick={() => setActiveTab('payments')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              activeTab === 'payments' 
                ? 'bg-blue-600 text-white' 
                : 'text-gray-300 hover:bg-gray-700'
            }`}
          >
            <CreditCard className="w-5 h-5" />
            <span>Payments</span>
          </button>
        </nav>

        <div className="p-4 border-t border-gray-700">
          <Button
            onClick={onLogout}
            variant="ghost"
            className="w-full flex items-center space-x-3 text-gray-300 hover:bg-gray-700"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl text-white">
                {activeTab === 'phones' && 'My Phones'}
                {activeTab === 'profile' && 'Profile'}
                {activeTab === 'payments' && 'Payments'}
              </h1>
              <p className="text-gray-400 text-sm">
                {activeTab === 'phones' && `Manage your virtual Android devices`}
                {activeTab === 'profile' && `Account information and statistics`}
                {activeTab === 'payments' && `Payment history and top-up options`}
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 bg-gray-700/50 px-4 py-2 rounded-lg">
                <DollarSign className="w-4 h-4 text-green-400" />
                <span className="text-white">{user.balance.toFixed(2)} USDT</span>
              </div>
              {activeTab === 'phones' && (
                <Button
                  onClick={onCreatePhone}
                  className="bg-blue-600 hover:bg-blue-700 flex items-center space-x-2"
                >
                  <Plus className="w-4 h-4" />
                  <span>New Phone</span>
                </Button>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {activeTab === 'phones' && (
            <div className="space-y-6">
              {/* Stats */}
              <div className="grid md:grid-cols-3 gap-6">
                <Card className="bg-gray-800 border-gray-700">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm text-gray-300">Active Phones</CardTitle>
                    <Activity className="h-4 w-4 text-green-400" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl text-white">{activePhones}</div>
                    <p className="text-xs text-gray-400">Currently running</p>
                  </CardContent>
                </Card>

                <Card className="bg-gray-800 border-gray-700">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm text-gray-300">Total Phones</CardTitle>
                    <Server className="h-4 w-4 text-blue-400" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl text-white">{phones.length}</div>
                    <p className="text-xs text-gray-400">All devices</p>
                  </CardContent>
                </Card>

                <Card className="bg-gray-800 border-gray-700">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm text-gray-300">Expired</CardTitle>
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl text-white">{expiredPhones}</div>
                    <p className="text-xs text-gray-400">Need top-up</p>
                  </CardContent>
                </Card>
              </div>

              {/* Phone List */}
              <div className="grid lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {phones.map((phone) => (
                  <Card key={phone.id} className="bg-gray-800 border-gray-700 hover:bg-gray-800/70 transition-colors">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-white flex items-center space-x-2">
                          <span className={`w-3 h-3 rounded-full ${getStatusColor(phone.status)}`}></span>
                          <span>{phone.name}</span>
                        </CardTitle>
                        {getStatusIcon(phone.status)}
                      </div>
                      <CardDescription className="text-gray-400">
                        {phone.model} • {phone.apiLevel}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {phone.status === 'active' && (
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-400">Time remaining</span>
                            <span className="text-white">{formatTimeRemaining(phone.timeRemaining)}</span>
                          </div>
                          <Progress 
                            value={(phone.timeRemaining / 24) * 100} 
                            className="h-2"
                          />
                        </div>
                      )}

                      {phone.status === 'expired' && (
                        <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-3">
                          <div className="flex items-center space-x-2 text-red-400 text-sm">
                            <AlertTriangle className="w-4 h-4" />
                            <span>Phone expired - Top up to reactivate</span>
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between text-sm text-gray-400">
                        <span>Cost: 1 USDT/day</span>
                        <Badge variant="outline" className="border-gray-600 text-gray-400">
                          {phone.status}
                        </Badge>
                      </div>

                      <div className="flex space-x-2">
                        <Button
                          onClick={() => onPhoneDetails(phone)}
                          variant="outline"
                          size="sm"
                          className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-700"
                        >
                          Details
                        </Button>
                        <Button
                          onClick={() => onTopUp(phone.id)}
                          size="sm"
                          className={`flex-1 flex items-center space-x-1 ${
                            phone.status === 'expired' 
                              ? 'bg-red-600 hover:bg-red-700' 
                              : 'bg-blue-600 hover:bg-blue-700'
                          }`}
                        >
                          <Zap className="w-3 h-3" />
                          <span>Top Up</span>
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {phones.length === 0 && (
                  <div className="col-span-full text-center py-12">
                    <Smartphone className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl text-white mb-2">No phones yet</h3>
                    <p className="text-gray-400 mb-6">Create your first virtual Android phone to get started</p>
                    <Button onClick={onCreatePhone} className="bg-blue-600 hover:bg-blue-700">
                      <Plus className="w-4 h-4 mr-2" />
                      Create Phone
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="max-w-2xl space-y-6">
              <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">Account Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-4">
                    <Avatar className="w-16 h-16">
                      <AvatarFallback className="bg-blue-600 text-white text-xl">
                        {user.telegramUsername.charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <h3 className="text-xl text-white">@{user.telegramUsername}</h3>
                      <p className="text-gray-400">Telegram Account</p>
                    </div>
                  </div>
                  <Separator className="bg-gray-700" />
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-gray-400 text-sm">Total Phones</p>
                      <p className="text-white text-xl">{user.totalPhones}</p>
                    </div>
                    <div>
                      <p className="text-gray-400 text-sm">Total Spent</p>
                      <p className="text-white text-xl">{user.totalSpent} USDT</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">Current Balance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl text-green-400 mb-2">{user.balance.toFixed(2)} USDT</div>
                  <p className="text-gray-400">Available for phone usage</p>
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'payments' && (
            <div className="space-y-6">
              <Card className="bg-gray-800 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">Payment History</CardTitle>
                  <CardDescription className="text-gray-400">Recent transactions</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="flex items-center justify-between py-3 border-b border-gray-700 last:border-0">
                        <div className="flex items-center space-x-3">
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                          <div>
                            <p className="text-white text-sm">Top-up for Android Testing Phone</p>
                            <p className="text-gray-400 text-xs">2025-01-{21-i} 14:30</p>
                          </div>
                        </div>
                        <span className="text-green-400">+{(1 + Math.random() * 5).toFixed(2)} USDT</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}