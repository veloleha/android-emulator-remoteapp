import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Separator } from './ui/separator';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Send, Shield, Clock, CreditCard, Smartphone, Server, Zap } from 'lucide-react';

interface HomepageProps {
  onLogin: () => void;
}

export function Homepage({ onLogin }: HomepageProps) {
  const features = [
    {
      icon: <Shield className="w-8 h-8 text-blue-400" />,
      title: "Secure Emulators",
      description: "Isolated virtual Android environments with enterprise-grade security"
    },
    {
      icon: <Clock className="w-8 h-8 text-green-400" />,
      title: "Real-time Timers",
      description: "Track usage with precision and receive alerts before expiration"
    },
    {
      icon: <CreditCard className="w-8 h-8 text-purple-400" />,
      title: "USDT Payments",
      description: "Seamless cryptocurrency payments for global accessibility"
    },
    {
      icon: <Server className="w-8 h-8 text-cyan-400" />,
      title: "High Performance",
      description: "Premium cloud infrastructure for smooth Android experience"
    }
  ];

  const faqs = [
    {
      question: "How do I get started?",
      answer: "Simply register with your Telegram account and create your first virtual phone. No email or complex verification required."
    },
    {
      question: "What payment methods do you accept?",
      answer: "We accept USDT payments for global accessibility and instant transactions."
    },
    {
      question: "Can I use multiple phones simultaneously?",
      answer: "Yes, you can create and manage multiple virtual Android phones from your dashboard."
    },
    {
      question: "What happens when my time expires?",
      answer: "Your phone will be automatically suspended. Simply top up your balance to reactivate it."
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900">
      {/* Header */}
      <header className="bg-gray-900/50 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-2">
              <Smartphone className="w-8 h-8 text-blue-400" />
              <span className="text-2xl text-white">Phone Emulator Hub</span>
            </div>
            <Button 
              onClick={onLogin}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center space-x-2"
            >
              <Send className="w-4 h-4" />
              <span>Register with Telegram</span>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <h1 className="text-5xl lg:text-6xl text-white leading-tight">
                  Launch your own
                  <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"> virtual Android phone</span>
                </h1>
                <p className="text-xl text-gray-300 leading-relaxed">
                  Perfect for testing, development, or remote Android access. Get started with just 1 USDT per day per phone.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  onClick={onLogin}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg flex items-center justify-center space-x-3"
                >
                  <Send className="w-5 h-5" />
                  <span>Register with Telegram</span>
                </Button>
                <Button 
                  variant="outline" 
                  size="lg"
                  className="border-gray-600 text-gray-300 hover:bg-gray-800 px-8 py-4 rounded-lg"
                >
                  Learn More
                </Button>
              </div>

              <div className="flex items-center space-x-6 text-gray-400">
                <div className="flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-green-400" />
                  <span>Instant Setup</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Shield className="w-5 h-5 text-blue-400" />
                  <span>Secure Access</span>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="relative z-10">
                <ImageWithFallback 
                  src="https://images.unsplash.com/photo-1650234083203-41aaf2cfeae6?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2JpbGUlMjBwaG9uZSUyMGVtdWxhdG9yJTIwYW5kcm9pZHxlbnwxfHx8fDE3NTg0ODYzMDJ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral"
                  alt="Android Emulator Interface"
                  className="w-full h-auto rounded-2xl shadow-2xl"
                />
              </div>
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 to-purple-500/20 rounded-2xl blur-3xl"></div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl text-white mb-4">Powerful Features</h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Everything you need to run virtual Android phones in the cloud
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="bg-gray-800/50 border-gray-700 hover:bg-gray-800/70 transition-colors">
                <CardHeader className="text-center">
                  <div className="mx-auto mb-4 p-3 bg-gray-700/50 rounded-lg w-fit">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-white">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-gray-400 text-center">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl text-white mb-8">Simple Pricing</h2>
          
          <Card className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 border-gray-700 max-w-md mx-auto">
            <CardHeader className="text-center pb-8">
              <CardTitle className="text-3xl text-white mb-2">Pay Per Use</CardTitle>
              <div className="text-5xl text-white mb-2">
                <span className="text-green-400">1</span> USDT
              </div>
              <CardDescription className="text-gray-400">per day, per phone</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>24-hour access period</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Full Android environment</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Real-time monitoring</span>
              </div>
              <div className="flex items-center space-x-3 text-gray-300">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <span>Instant activation</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-900/50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl text-white mb-4">Frequently Asked Questions</h2>
          </div>

          <div className="space-y-6">
            {faqs.map((faq, index) => (
              <Card key={index} className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">{faq.question}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-400">{faq.answer}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 border-t border-gray-800 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <Smartphone className="w-6 h-6 text-blue-400" />
              <span className="text-xl text-white">Phone Emulator Hub</span>
            </div>
            <div className="text-gray-400 text-center md:text-right">
              <p>&copy; 2025 Phone Emulator Hub. All rights reserved.</p>
              <p className="text-sm mt-1">Secure virtual Android phones powered by USDT</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}