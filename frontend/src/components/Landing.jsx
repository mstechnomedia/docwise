import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Landing = ({ onLogin }) => {
  const [showAuth, setShowAuth] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: ''
  });

  const handleGoogleLogin = () => {
    const redirectUrl = `${window.location.origin}/dashboard`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const handleFormSubmit = async (e, isLogin) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;
      
      const response = await axios.post(`${API}${endpoint}`, payload);
      
      onLogin(response.data.user, response.data.session_token);
      setShowAuth(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const features = [
    {
      icon: 'fas fa-file-pdf',
      title: 'Advanced PDF Processing',
      description: 'Extract text, tables, images, and formatting from any PDF document with high accuracy.'
    },
    {
      icon: 'fas fa-robot',
      title: 'Multiple AI Models',
      description: 'Choose between GPT-5 and Claude-4 for tailored document analysis and insights.'
    },
    {
      icon: 'fas fa-edit',
      title: 'Custom Prompts',
      description: 'Create, save, and edit analysis prompts to get exactly the information you need.'
    },
    {
      icon: 'fas fa-download',
      title: 'Export & Share',
      description: 'Copy responses to clipboard or download comprehensive analysis reports.'
    },
    {
      icon: 'fas fa-shield-alt',
      title: 'Secure & Private',
      description: 'Your documents and analyses are encrypted and stored securely with user authentication.'
    },
    {
      icon: 'fas fa-bolt',
      title: 'Fast Processing',
      description: 'Get detailed document insights in seconds with our optimized AI processing pipeline.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* Navigation */}
      <nav className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-800 to-slate-600 rounded-xl flex items-center justify-center">
                <i className="fas fa-file-text text-white text-lg"></i>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800 font-space">Manuscript-TM</h1>
                <p className="text-sm text-slate-500 font-medium">DocWise</p>
              </div>
            </div>
            <Button 
              data-testid="get-started-btn"
              onClick={() => setShowAuth(true)}
              className="btn-primary"
            >
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-20 pb-32 relative overflow-hidden">
        <div className="absolute inset-0 bg-noise opacity-5"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-5xl lg:text-6xl font-bold text-slate-800 font-space mb-6 animate-slide-up">
              AI-Powered Document Analysis
            </h1>
            <p className="text-xl lg:text-2xl text-slate-600 mb-8 leading-relaxed animate-slide-up" style={{animationDelay: '0.2s'}}>
              Extract insights from PDF documents with advanced AI. Create custom prompts, 
              choose your preferred AI model, and get comprehensive analysis in seconds.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-slide-up" style={{animationDelay: '0.4s'}}>
              <Button 
                onClick={() => setShowAuth(true)}
                className="btn-primary text-lg px-8 py-4"
                data-testid="hero-get-started-btn"
              >
                <i className="fas fa-rocket mr-2"></i>
                Start Analyzing Documents
              </Button>
              <Button 
                variant="outline" 
                className="btn-secondary text-lg px-8 py-4"
                onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}
              >
                <i className="fas fa-info-circle mr-2"></i>
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-slate-50/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-800 font-space mb-4">
              Powerful Features for Document Analysis
            </h2>
            <p className="text-xl text-slate-600 max-w-3xl mx-auto">
              Everything you need to extract, analyze, and understand your PDF documents using cutting-edge AI technology.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                className="card-hover bg-white/80 backdrop-blur-sm border-slate-200/50 animate-fade-in-scale"
                style={{animationDelay: `${index * 0.1}s`}}
              >
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-gradient-to-br from-slate-800 to-slate-600 rounded-xl flex items-center justify-center mb-4">
                    <i className={`${feature.icon} text-white text-xl`}></i>
                  </div>
                  <h3 className="text-xl font-semibold text-slate-800 mb-3 font-space">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-gradient-to-br from-slate-800 to-slate-700 relative overflow-hidden">
        <div className="absolute inset-0 bg-noise opacity-10"></div>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative text-center">
          <h2 className="text-4xl lg:text-5xl font-bold text-white font-space mb-6">
            Ready to Transform Your Document Workflow?
          </h2>
          <p className="text-xl text-slate-300 mb-8 max-w-3xl mx-auto leading-relaxed">
            Join professionals who trust Manuscript-TM DocWise for intelligent document analysis. 
            Start extracting insights from your PDFs today.
          </p>
          <Button 
            onClick={() => setShowAuth(true)}
            className="bg-white text-slate-800 hover:bg-slate-100 text-lg px-8 py-4 font-semibold"
            data-testid="cta-get-started-btn"
          >
            <i className="fas fa-arrow-right mr-2"></i>
            Get Started Free
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-gradient-to-br from-slate-600 to-slate-500 rounded-lg flex items-center justify-center">
                <i className="fas fa-file-text text-white text-sm"></i>
              </div>
              <span className="text-lg font-semibold text-slate-300">Manuscript-TM DocWise</span>
            </div>
            <p className="text-sm">
              © 2025 Manuscript-TM DocWise. Powered by advanced AI technology.
            </p>
          </div>
        </div>
      </footer>

      {/* Authentication Modal */}
      <Dialog open={showAuth} onOpenChange={setShowAuth}>
        <DialogContent className="sm:max-w-md" data-testid="auth-modal">
          <DialogHeader>
            <DialogTitle className="text-2xl font-semibold text-slate-800 text-center font-space">
              Welcome to DocWise
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Google Login */}
            <Button 
              onClick={handleGoogleLogin}
              className="btn-google w-full"
              data-testid="google-login-btn"
            >
              <i className="fab fa-google text-lg"></i>
              Continue with Google
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-slate-500">or</span>
              </div>
            </div>

            {/* Login/Register Forms */}
            <Tabs defaultValue="login" className="space-y-4">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login" data-testid="login-tab">Login</TabsTrigger>
                <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
              </TabsList>
              
              <TabsContent value="login">
                <form onSubmit={(e) => handleFormSubmit(e, true)} className="space-y-4">
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                      className="input-focus"
                      data-testid="login-email-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                      className="input-focus"
                      data-testid="login-password-input"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full btn-primary"
                    disabled={loading}
                    data-testid="login-submit-btn"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Logging in...
                      </>
                    ) : (
                      'Login'
                    )}
                  </Button>
                </form>
              </TabsContent>
              
              <TabsContent value="register">
                <form onSubmit={(e) => handleFormSubmit(e, false)} className="space-y-4">
                  <div>
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      name="name"
                      value={formData.name}
                      onChange={handleInputChange}
                      required
                      className="input-focus"
                      data-testid="register-name-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      name="email"
                      type="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      required
                      className="input-focus"
                      data-testid="register-email-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      required
                      className="input-focus"
                      data-testid="register-password-input"
                    />
                  </div>
                  <Button 
                    type="submit" 
                    className="w-full btn-primary"
                    disabled={loading}
                    data-testid="register-submit-btn"
                  >
                    {loading ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Creating account...
                      </>
                    ) : (
                      'Create Account'
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Landing;
