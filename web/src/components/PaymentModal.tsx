import React, { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Wallet, 
  QrCode, 
  Copy, 
  ExternalLink, 
  CreditCard, 
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react';
import { Phone } from '../App';

interface PaymentModalProps {
  phone: Phone;
  onClose: () => void;
}

export function PaymentModal({ phone, onClose }: PaymentModalProps) {
  const [paymentMethod, setPaymentMethod] = useState<'wallet' | 'metamask'>('wallet');
  const [paymentStatus, setPaymentStatus] = useState<'idle' | 'processing' | 'success'>('idle');

  const usdtWalletAddress = "TKzxrLkU5d5z6Q8fJ9L2VwXhF7M8K3P2N1";
  const paymentAmount = phone.status === 'expired' ? 1.0 : 1.0; // Same cost for top-up

  const handleCopyAddress = () => {
    navigator.clipboard.writeText(usdtWalletAddress);
  };

  const handleMetaMaskPayment = () => {
    setPaymentStatus('processing');
    // Simulate MetaMask payment
    setTimeout(() => {
      setPaymentStatus('success');
    }, 3000);
  };

  const handleManualPayment = () => {
    setPaymentStatus('processing');
    // Simulate manual payment verification
    setTimeout(() => {
      setPaymentStatus('success');
    }, 5000);
  };

  if (paymentStatus === 'success') {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="sm:max-w-md bg-gray-900 border-gray-700">
          <div className="text-center space-y-6 py-6">
            <div className="mx-auto w-16 h-16 bg-green-600 rounded-full flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-white" />
            </div>
            <div className="space-y-2">
              <h3 className="text-xl text-white">Payment Successful!</h3>
              <p className="text-gray-400">
                {phone.name} has been topped up with 24 hours of usage time.
              </p>
            </div>
            <Button onClick={onClose} className="bg-blue-600 hover:bg-blue-700">
              Continue
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={true} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl bg-gray-900 border-gray-700">
        <DialogHeader>
          <DialogTitle className="text-white flex items-center space-x-2">
            <Wallet className="w-5 h-5 text-green-400" />
            <span>Top Up Phone</span>
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Add usage time to {phone.name}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Phone Info */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white">{phone.name}</h4>
                  <p className="text-gray-400 text-sm">{phone.model} • {phone.apiLevel}</p>
                </div>
                <Badge variant={phone.status === 'active' ? 'default' : 'destructive'}>
                  {phone.status}
                </Badge>
              </div>
              {phone.status === 'expired' && (
                <div className="mt-3 flex items-center space-x-2 text-red-400 text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Phone is expired and needs immediate top-up</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Payment Summary */}
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Payment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Usage time</span>
                <span className="text-white">24 hours</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Rate</span>
                <span className="text-white">1 USDT per day</span>
              </div>
              <Separator className="bg-gray-700" />
              <div className="flex justify-between">
                <span className="text-white">Total</span>
                <span className="text-green-400 text-lg">{paymentAmount.toFixed(2)} USDT</span>
              </div>
            </CardContent>
          </Card>

          {/* Payment Methods */}
          {paymentStatus === 'idle' && (
            <Tabs value={paymentMethod} onValueChange={(value) => setPaymentMethod(value as 'wallet' | 'metamask')}>
              <TabsList className="grid w-full grid-cols-2 bg-gray-800 border-gray-700">
                <TabsTrigger value="wallet" className="text-gray-300">Wallet Transfer</TabsTrigger>
                <TabsTrigger value="metamask" className="text-gray-300">MetaMask</TabsTrigger>
              </TabsList>

              <TabsContent value="wallet" className="space-y-4">
                <Card className="bg-gray-800 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <QrCode className="w-5 h-5" />
                      <span>USDT (TRC-20) Wallet</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Send exactly {paymentAmount.toFixed(2)} USDT to the address below
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="bg-gray-900/50 rounded-lg p-4 space-y-3">
                      <div className="text-center">
                        <div className="bg-white p-4 rounded-lg inline-block">
                          <div className="w-32 h-32 bg-gray-800 rounded flex items-center justify-center">
                            <QrCode className="w-16 h-16 text-gray-400" />
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <p className="text-gray-400 text-sm text-center">Wallet Address:</p>
                        <div className="flex items-center space-x-2 bg-gray-800 rounded-lg p-3">
                          <code className="flex-1 text-white text-sm break-all">
                            {usdtWalletAddress}
                          </code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={handleCopyAddress}
                            className="text-gray-400 hover:text-white"
                          >
                            <Copy className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
                      <div className="flex items-start space-x-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-400 mt-0.5" />
                        <div className="text-yellow-200 text-sm">
                          <p className="font-medium">Important:</p>
                          <ul className="mt-1 space-y-1 text-xs">
                            <li>• Only send USDT on TRC-20 network</li>
                            <li>• Send exactly {paymentAmount.toFixed(2)} USDT</li>
                            <li>• Processing takes 1-5 minutes</li>
                          </ul>
                        </div>
                      </div>
                    </div>

                    <Button
                      onClick={handleManualPayment}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      I've Sent the Payment
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="metamask" className="space-y-4">
                <Card className="bg-gray-800 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center space-x-2">
                      <img 
                        src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHZpZXdCb3g9IjAgMCAzMiAzMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iOCIgZmlsbD0iI0Y2ODUxQiIvPgo8L3N2Zz4K" 
                        alt="MetaMask" 
                        className="w-5 h-5"
                      />
                      <span>MetaMask Payment</span>
                    </CardTitle>
                    <CardDescription className="text-gray-400">
                      Connect your MetaMask wallet for instant payment
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="text-center space-y-4">
                      <div className="bg-gray-900/50 rounded-lg p-6">
                        <CreditCard className="w-12 h-12 text-orange-400 mx-auto mb-3" />
                        <p className="text-white">Pay {paymentAmount.toFixed(2)} USDT</p>
                        <p className="text-gray-400 text-sm">Instant confirmation</p>
                      </div>
                      
                      <Button
                        onClick={handleMetaMaskPayment}
                        className="w-full bg-orange-600 hover:bg-orange-700 flex items-center space-x-2"
                      >
                        <span>Connect MetaMask</span>
                        <ExternalLink className="w-4 h-4" />
                      </Button>
                    </div>

                    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3">
                      <div className="flex items-start space-x-2">
                        <CheckCircle className="w-4 h-4 text-blue-400 mt-0.5" />
                        <div className="text-blue-200 text-sm">
                          <p className="font-medium">Benefits:</p>
                          <ul className="mt-1 space-y-1 text-xs">
                            <li>• Instant payment confirmation</li>
                            <li>• Automatic phone activation</li>
                            <li>• Secure smart contract</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}

          {paymentStatus === 'processing' && (
            <Card className="bg-gray-800 border-gray-700">
              <CardContent className="p-8 text-center space-y-4">
                <div className="mx-auto w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center animate-pulse">
                  <Clock className="w-8 h-8 text-white" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg text-white">Processing Payment</h3>
                  <p className="text-gray-400">
                    {paymentMethod === 'metamask' 
                      ? 'Confirming transaction on blockchain...' 
                      : 'Waiting for payment confirmation...'}
                  </p>
                </div>
                <div className="flex justify-center">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {paymentStatus === 'idle' && (
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={onClose}
                className="flex-1 border-gray-600 text-gray-300 hover:bg-gray-800"
              >
                Cancel
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}