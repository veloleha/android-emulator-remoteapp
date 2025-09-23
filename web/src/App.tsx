import React, { useState, useEffect } from 'react';
import { Homepage } from './components/Homepage';
import { Dashboard } from './components/Dashboard';
import { LoginModal } from './components/LoginModal';
import { CreatePhoneModal } from './components/CreatePhoneModal';
import { PaymentModal } from './components/PaymentModal';
import { PhoneDetailsModal } from './components/PhoneDetailsModal';

export interface Phone {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'expired';
  timeRemaining: number; // in hours
  model: string;
  apiLevel: string;
  createdAt: Date;
  lastPayment: Date;
}

export interface User {
  id: string;
  telegramUsername: string;
  balance: number;
  totalPhones: number;
  totalSpent: number;
}

export default function App() {
  const [currentScreen, setCurrentScreen] = useState<'homepage' | 'dashboard'>('homepage');
  const [user, setUser] = useState<User | null>(null);
  const [phones, setPhones] = useState<Phone[]>([]);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showCreatePhoneModal, setShowCreatePhoneModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showPhoneDetailsModal, setShowPhoneDetailsModal] = useState(false);
  const [selectedPhone, setSelectedPhone] = useState<Phone | null>(null);

  // Mock login function
  const handleLogin = (username: string) => {
    const mockUser: User = {
      id: '1',
      telegramUsername: username,
      balance: 25.5,
      totalPhones: 3,
      totalSpent: 156.7
    };
    setUser(mockUser);
    setCurrentScreen('dashboard');
    setShowLoginModal(false);
    
    // Load mock phones
    const mockPhones: Phone[] = [
      {
        id: '1',
        name: 'Android Testing Phone',
        status: 'active',
        timeRemaining: 23.75,
        model: 'Pixel 6',
        apiLevel: 'API 33',
        createdAt: new Date('2025-01-20'),
        lastPayment: new Date('2025-01-21')
      },
      {
        id: '2',
        name: 'Development Device',
        status: 'active',
        timeRemaining: 8.2,
        model: 'Samsung Galaxy S21',
        apiLevel: 'API 31',
        createdAt: new Date('2025-01-19'),
        lastPayment: new Date('2025-01-21')
      },
      {
        id: '3',
        name: 'Legacy Testing',
        status: 'expired',
        timeRemaining: 0,
        model: 'Pixel 4',
        apiLevel: 'API 29',
        createdAt: new Date('2025-01-18'),
        lastPayment: new Date('2025-01-20')
      }
    ];
    setPhones(mockPhones);
  };

  const handleCreatePhone = (phoneData: { name: string; model: string; apiLevel: string }) => {
    const newPhone: Phone = {
      id: Date.now().toString(),
      name: phoneData.name,
      status: 'active',
      timeRemaining: 24,
      model: phoneData.model,
      apiLevel: phoneData.apiLevel,
      createdAt: new Date(),
      lastPayment: new Date()
    };
    setPhones([...phones, newPhone]);
    setShowCreatePhoneModal(false);
  };

  const handleTopUp = (phoneId: string) => {
    setSelectedPhone(phones.find(p => p.id === phoneId) || null);
    setShowPaymentModal(true);
  };

  const handlePhoneDetails = (phone: Phone) => {
    setSelectedPhone(phone);
    setShowPhoneDetailsModal(true);
  };

  const handleLogout = () => {
    setUser(null);
    setPhones([]);
    setCurrentScreen('homepage');
  };

  // Timer countdown effect
  useEffect(() => {
    if (user && phones.length > 0) {
      const timer = setInterval(() => {
        setPhones(prevPhones => 
          prevPhones.map(phone => {
            if (phone.status === 'active' && phone.timeRemaining > 0) {
              const newTimeRemaining = Math.max(0, phone.timeRemaining - (1/3600)); // Decrease by 1 second
              return {
                ...phone,
                timeRemaining: newTimeRemaining,
                status: newTimeRemaining <= 0 ? 'expired' : 'active'
              };
            }
            return phone;
          })
        );
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [user, phones.length]);

  return (
    <div className="min-h-screen bg-gray-900">
      {currentScreen === 'homepage' ? (
        <Homepage onLogin={() => setShowLoginModal(true)} />
      ) : (
        <Dashboard
          user={user!}
          phones={phones}
          onCreatePhone={() => setShowCreatePhoneModal(true)}
          onTopUp={handleTopUp}
          onPhoneDetails={handlePhoneDetails}
          onLogout={handleLogout}
        />
      )}

      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onLogin={handleLogin}
        />
      )}

      {showCreatePhoneModal && (
        <CreatePhoneModal
          onClose={() => setShowCreatePhoneModal(false)}
          onCreate={handleCreatePhone}
        />
      )}

      {showPaymentModal && selectedPhone && (
        <PaymentModal
          phone={selectedPhone}
          onClose={() => setShowPaymentModal(false)}
        />
      )}

      {showPhoneDetailsModal && selectedPhone && (
        <PhoneDetailsModal
          phone={selectedPhone}
          onClose={() => setShowPhoneDetailsModal(false)}
        />
      )}
    </div>
  );
}