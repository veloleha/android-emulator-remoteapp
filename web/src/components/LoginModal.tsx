import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Send, Shield, CheckCircle } from 'lucide-react';

interface LoginModalProps {
  onClose: () => void;
  onLogin: (username: string) => void;
}

export function LoginModal({ onClose, onLogin }: LoginModalProps) {
  const [step, setStep] = useState<'telegram' | 'verification' | 'success'>('telegram');
  const [username, setUsername] = useState('');

  const handleTelegramLogin = () => {
    setStep('verification');
    // Simulate verification process
    setTimeout(() => {
      setStep('success');
      setTimeout(() => {
        onLogin(username || 'demo_user');
      }, 1500);
    }, 2000);
  };

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center space-x-2">
            <Send className="w-5 h-5 text-blue-400" />
            <span>Login with Telegram</span>
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            {step === 'telegram' && "Connect your Telegram account to get started"}
            {step === 'verification' && "Verifying your Telegram account..."}
            {step === 'success' && "Successfully connected!"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {step === 'telegram' && (
            <>
              <div className="space-y-4">
                <div className="text-center">
                  <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4">
                    <Send className="w-8 h-8 text-white" />
                  </div>
                  <p className="text-gray-300">
                    We'll redirect you to Telegram to verify your account. 
                    No email or password required.
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="username" className="text-gray-300">
                    Telegram Username (optional preview)
                  </Label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">@</span>
                    <Input
                      id="username"
                      placeholder="your_username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-8 bg-gray-800 border-gray-600 text-white placeholder-gray-500"
                    />
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-lg p-4 space-y-2">
                  <div className="flex items-center space-x-2 text-green-400 text-sm">
                    <Shield className="w-4 h-4" />
                    <span>Secure Authentication</span>
                  </div>
                  <p className="text-gray-400 text-sm">
                    We use Telegram's official login system. Your data is never stored on our servers.
                  </p>
                </div>
              </div>

              <Button 
                onClick={handleTelegramLogin}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg flex items-center justify-center space-x-2"
              >
                <Send className="w-4 h-4" />
                <span>Continue with Telegram</span>
              </Button>
            </>
          )}

          {step === 'verification' && (
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mb-4 animate-pulse">
                <Send className="w-8 h-8 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg text-white">Connecting to Telegram...</h3>
                <p className="text-gray-400">
                  Please check your Telegram app and confirm the login request.
                </p>
              </div>
              <div className="flex justify-center">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}

          {step === 'success' && (
            <div className="text-center space-y-4">
              <div className="mx-auto w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-white" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg text-white">Welcome!</h3>
                <p className="text-gray-400">
                  Logged in as @{username || 'demo_user'}
                </p>
                <p className="text-gray-500 text-sm">
                  Redirecting to your dashboard...
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            By logging in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}