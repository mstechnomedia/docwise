import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('prompts');
  const [prompts, setPrompts] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [promptForm, setPromptForm] = useState({ title: '', content: '' });
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisForm, setAnalysisForm] = useState({ prompt_id: '', ai_model: 'gpt-5' });
  const [analyzing, setAnalyzing] = useState(false);
  const [inputMode, setInputMode] = useState('upload'); // 'upload' or 'text'
  const [textInput, setTextInput] = useState('');

  useEffect(() => {
    loadPrompts();
    loadAnalyses();
  }, []);

  const loadPrompts = async () => {
    try {
      const response = await axios.get(`${API}/prompts`);
      setPrompts(response.data);
    } catch (error) {
      toast.error('Failed to load prompts');
    }
  };

  const loadAnalyses = async () => {
    try {
      const response = await axios.get(`${API}/documents/analyses`);
      setAnalyses(response.data);
    } catch (error) {
      toast.error('Failed to load analyses');
    }
  };

  const handlePromptSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (editingPrompt) {
        await axios.put(`${API}/prompts/${editingPrompt.id}`, promptForm);
        toast.success('Prompt updated successfully');
      } else {
        await axios.post(`${API}/prompts`, promptForm);
        toast.success('Prompt created successfully');
      }
      
      setShowPromptModal(false);
      setEditingPrompt(null);
      setPromptForm({ title: '', content: '' });
      loadPrompts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePrompt = async (promptId) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return;
    
    try {
      await axios.delete(`${API}/prompts/${promptId}`);
      toast.success('Prompt deleted successfully');
      loadPrompts();
    } catch (error) {
      toast.error('Failed to delete prompt');
    }
  };

  const handleEditPrompt = (prompt) => {
    setEditingPrompt(prompt);
    setPromptForm({ title: prompt.title, content: prompt.content });
    setShowPromptModal(true);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        toast.error('Please select a PDF file');
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleAnalyzeDocument = async (e) => {
    e.preventDefault();
    
    if (inputMode === 'upload' && (!selectedFile || !analysisForm.prompt_id)) {
      toast.error('Please select a file and prompt');
      return;
    }
    
    if (inputMode === 'text' && (!textInput.trim() || !analysisForm.prompt_id)) {
      toast.error('Please enter text content and select a prompt');
      return;
    }
    
    setAnalyzing(true);
    
    try {
      let response;
      
      if (inputMode === 'upload') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('analysis_data', JSON.stringify(analysisForm));
        
        response = await axios.post(`${API}/documents/analyze`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      } else {
        // Text input mode
        const textAnalysisData = {
          ...analysisForm,
          text_content: textInput,
          document_name: 'Text Input'
        };
        
        response = await axios.post(`${API}/documents/analyze-text`, textAnalysisData, {
          headers: {
            'Content-Type': 'application/json'
          }
        });
      }
      
      toast.success('Content analyzed successfully!');
      setSelectedFile(null);
      setTextInput('');
      setAnalysisForm({ prompt_id: '', ai_model: 'gpt-5' });
      loadAnalyses();
      setActiveTab('analyses');
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleCopyResponse = (response) => {
    navigator.clipboard.writeText(response);
    toast.success('Response copied to clipboard!');
  };

  const handleDownloadAnalysis = async (analysisId) => {
    try {
      const response = await axios.get(`${API}/documents/analyses/${analysisId}/download`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `analysis_${analysisId}.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Analysis downloaded!');
    } catch (error) {
      toast.error('Failed to download analysis');
    }
  };

  const tabs = [
    { id: 'prompts', label: 'Prompts', icon: 'fas fa-edit' },
    { id: 'analyze', label: 'Analyze Document', icon: 'fas fa-file-upload' },
    { id: 'analyses', label: 'Analysis History', icon: 'fas fa-history' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-800 to-slate-600 rounded-xl flex items-center justify-center">
                <i className="fas fa-file-text text-white text-lg"></i>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800 font-space">Manuscript-TM</h1>
                <p className="text-sm text-slate-500 font-medium">DocWise Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-slate-600">
                <img 
                  src={user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=1e293b&color=fff`}
                  alt={user.name}
                  className="w-8 h-8 rounded-full"
                />
                <span className="font-medium">{user.name}</span>
              </div>
              <Button 
                variant="outline" 
                onClick={onLogout}
                className="btn-secondary"
                data-testid="logout-btn"
              >
                <i className="fas fa-sign-out-alt mr-2"></i>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation Tabs */}
        <div className="mb-8">
          <nav className="flex space-x-8" data-testid="dashboard-tabs">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
                data-testid={`${tab.id}-tab`}
              >
                <i className={`${tab.icon} mr-2`}></i>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Prompts Tab */}
        {activeTab === 'prompts' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-slate-800 font-space">Analysis Prompts</h2>
              <Dialog open={showPromptModal} onOpenChange={setShowPromptModal}>
                <DialogTrigger asChild>
                  <Button className="btn-primary" data-testid="create-prompt-btn">
                    <i className="fas fa-plus mr-2"></i>
                    Create Prompt
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-2xl">
                  <DialogHeader>
                    <DialogTitle className="font-space">
                      {editingPrompt ? 'Edit Prompt' : 'Create New Prompt'}
                    </DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handlePromptSubmit} className="space-y-4">
                    <div>
                      <Label htmlFor="title">Prompt Title</Label>
                      <Input
                        id="title"
                        value={promptForm.title}
                        onChange={(e) => setPromptForm(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="e.g., Extract Key Financial Metrics"
                        required
                        data-testid="prompt-title-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="content">Prompt Content</Label>
                      <Textarea
                        id="content"
                        value={promptForm.content}
                        onChange={(e) => setPromptForm(prev => ({ ...prev, content: e.target.value }))}
                        placeholder="Describe what information you want to extract from documents..."
                        rows={6}
                        required
                        data-testid="prompt-content-textarea"
                      />
                    </div>
                    <div className="flex justify-end space-x-2">
                      <Button 
                        type="button" 
                        variant="outline"
                        onClick={() => {
                          setShowPromptModal(false);
                          setEditingPrompt(null);
                          setPromptForm({ title: '', content: '' });
                        }}
                      >
                        Cancel
                      </Button>
                      <Button 
                        type="submit" 
                        disabled={loading}
                        className="btn-primary"
                        data-testid="save-prompt-btn"
                      >
                        {loading ? 'Saving...' : (editingPrompt ? 'Update' : 'Create')}
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {prompts.map(prompt => (
                <Card key={prompt.id} className="card-hover" data-testid="prompt-card">
                  <CardHeader>
                    <CardTitle className="text-lg font-space">{prompt.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-600 mb-4 line-clamp-3">{prompt.content}</p>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500">
                        {new Date(prompt.created_at).toLocaleDateString()}
                      </span>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleEditPrompt(prompt)}
                          data-testid="edit-prompt-btn"
                        >
                          <i className="fas fa-edit"></i>
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => handleDeletePrompt(prompt.id)}
                          className="text-red-600 hover:text-red-700"
                          data-testid="delete-prompt-btn"
                        >
                          <i className="fas fa-trash"></i>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {prompts.length === 0 && (
              <Card className="text-center py-12" data-testid="no-prompts-message">
                <CardContent>
                  <i className="fas fa-edit text-4xl text-slate-400 mb-4"></i>
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">No prompts yet</h3>
                  <p className="text-slate-500">Create your first analysis prompt to get started.</p>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Analyze Document Tab */}
        {activeTab === 'analyze' && (
          <div className="max-w-2xl mx-auto">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-space text-center">Analyze Content</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleAnalyzeDocument} className="space-y-6">
                  {/* Input Mode Selection */}
                  <div>
                    <Label className="text-base font-medium">Input Method</Label>
                    <div className="mt-3 flex space-x-4">
                      <button
                        type="button"
                        onClick={() => {setInputMode('upload'); setTextInput(''); setSelectedFile(null);}}
                        className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                          inputMode === 'upload' 
                            ? 'border-slate-800 bg-slate-50 text-slate-800' 
                            : 'border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                        data-testid="upload-mode-btn"
                      >
                        <i className="fas fa-file-pdf text-xl mb-2"></i>
                        <p className="font-medium">Upload PDF</p>
                        <p className="text-sm opacity-75">Upload a PDF document</p>
                      </button>
                      <button
                        type="button"
                        onClick={() => {setInputMode('text'); setSelectedFile(null); setTextInput('');}}
                        className={`flex-1 p-4 rounded-lg border-2 transition-all ${
                          inputMode === 'text' 
                            ? 'border-slate-800 bg-slate-50 text-slate-800' 
                            : 'border-slate-200 text-slate-600 hover:border-slate-300'
                        }`}
                        data-testid="text-mode-btn"
                      >
                        <i className="fas fa-edit text-xl mb-2"></i>
                        <p className="font-medium">Enter Text</p>
                        <p className="text-sm opacity-75">Type or paste content</p>
                      </button>
                    </div>
                  </div>

                  {/* File Upload */}
                  {inputMode === 'upload' && (
                    <div>
                      <Label htmlFor="file">PDF Document</Label>
                      <div className="mt-2">
                        <input
                          id="file"
                          type="file"
                          accept=".pdf"
                          onChange={handleFileSelect}
                          className="hidden"
                          data-testid="file-input"
                        />
                        <div 
                          className="drop-zone p-8 text-center cursor-pointer"
                          onClick={() => document.getElementById('file').click()}
                        >
                          {selectedFile ? (
                            <div className="text-green-600">
                              <i className="fas fa-file-pdf text-2xl mb-2"></i>
                              <p className="font-medium">{selectedFile.name}</p>
                              <p className="text-sm text-slate-500">Click to change file</p>
                            </div>
                          ) : (
                            <div className="text-slate-500">
                              <i className="fas fa-cloud-upload-alt text-3xl mb-4"></i>
                              <p className="font-medium mb-2">Choose PDF file to analyze</p>
                              <p className="text-sm">Click here or drag and drop your PDF</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Text Input */}
                  {inputMode === 'text' && (
                    <div>
                      <Label htmlFor="textContent">Text Content</Label>
                      <Textarea
                        id="textContent"
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        placeholder="Paste or type your content here for analysis. This can be any text content including documents, articles, reports, or any other text you'd like to analyze..."
                        rows={12}
                        className="mt-2 resize-none"
                        data-testid="text-input-area"
                      />
                      <p className="text-sm text-slate-500 mt-2">
                        {textInput.length} characters
                      </p>
                    </div>
                  )}

                  {/* Prompt Selection */}
                  <div>
                    <Label htmlFor="prompt">Analysis Prompt</Label>
                    <Select 
                      value={analysisForm.prompt_id} 
                      onValueChange={(value) => setAnalysisForm(prev => ({ ...prev, prompt_id: value }))}
                    >
                      <SelectTrigger data-testid="prompt-select">
                        <SelectValue placeholder="Select a prompt for analysis" />
                      </SelectTrigger>
                      <SelectContent>
                        {prompts.map(prompt => (
                          <SelectItem key={prompt.id} value={prompt.id}>
                            {prompt.title}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* AI Model Selection */}
                  <div>
                    <Label htmlFor="model">AI Model</Label>
                    <Select 
                      value={analysisForm.ai_model} 
                      onValueChange={(value) => setAnalysisForm(prev => ({ ...prev, ai_model: value }))}
                    >
                      <SelectTrigger data-testid="model-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-5">
                          <div className="flex items-center">
                            <i className="fas fa-robot mr-2 text-blue-600"></i>
                            GPT-5 (OpenAI)
                          </div>
                        </SelectItem>
                        <SelectItem value="claude-4">
                          <div className="flex items-center">
                            <i className="fas fa-brain mr-2 text-purple-600"></i>
                            Claude-4 (Anthropic)
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full btn-primary"
                    disabled={analyzing || 
                      (inputMode === 'upload' && (!selectedFile || !analysisForm.prompt_id)) ||
                      (inputMode === 'text' && (!textInput.trim() || !analysisForm.prompt_id))
                    }
                    data-testid="analyze-btn"
                  >
                    {analyzing ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Analyzing Content...
                      </>
                    ) : (
                      <>
                        <i className="fas fa-magic mr-2"></i>
                        Analyze {inputMode === 'upload' ? 'Document' : 'Text'}
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Analysis History Tab */}
        {activeTab === 'analyses' && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-800 font-space">Analysis History</h2>
            
            <div className="space-y-4">
              {analyses.map(analysis => {
                const prompt = prompts.find(p => p.id === analysis.prompt_id);
                return (
                  <Card key={analysis.id} className="card-hover" data-testid="analysis-card">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg font-space">{analysis.document_name}</CardTitle>
                          <p className="text-sm text-slate-600 mt-1">
                            Prompt: {prompt?.title || 'Unknown'}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className={`${
                            analysis.ai_model === 'gpt-5' ? 'text-blue-600' : 'text-purple-600'
                          }`}>
                            <i className={`fas ${
                              analysis.ai_model === 'gpt-5' ? 'fa-robot' : 'fa-brain'
                            } mr-1`}></i>
                            {analysis.ai_model === 'gpt-5' ? 'GPT-5' : 'Claude-4'}
                          </Badge>
                          <span className="text-sm text-slate-500">
                            {new Date(analysis.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <Label className="text-sm font-medium text-slate-700">Analysis Response</Label>
                          <div className="mt-2 p-4 bg-slate-50 rounded-lg analysis-content">
                            <p className="text-slate-700 whitespace-pre-wrap">{analysis.response}</p>
                          </div>
                        </div>
                        
                        <Separator />
                        
                        <div className="flex justify-between items-center">
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleCopyResponse(analysis.response)}
                              data-testid="copy-response-btn"
                            >
                              <i className="fas fa-copy mr-2"></i>
                              Copy Response
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleDownloadAnalysis(analysis.id)}
                              data-testid="download-analysis-btn"
                            >
                              <i className="fas fa-download mr-2"></i>
                              Download
                            </Button>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {analyses.length === 0 && (
              <Card className="text-center py-12" data-testid="no-analyses-message">
                <CardContent>
                  <i className="fas fa-history text-4xl text-slate-400 mb-4"></i>
                  <h3 className="text-lg font-semibold text-slate-600 mb-2">No analyses yet</h3>
                  <p className="text-slate-500 mb-4">Upload and analyze your first PDF document to see results here.</p>
                  <Button 
                    onClick={() => setActiveTab('analyze')}
                    className="btn-primary"
                  >
                    <i className="fas fa-upload mr-2"></i>
                    Analyze Document
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
