'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, ArrowRight } from 'lucide-react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

export default function Home() {
  const router = useRouter();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file || !file.type.includes('pdf')) {
      alert('Please upload a PDF file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Simulate upload progress
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(interval);
            return prev;
          }
          return prev + 5;
        });
      }, 100);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      clearInterval(interval);
      setUploadProgress(100);

      // Get the document ID from response
      const { documentId } = await response.json();

      // Redirect to chat page
      router.push(`/chat?documentId=${documentId}`);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload file. Please try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [router]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] -mt-16">
      <div className="max-w-2xl w-full px-4 space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
            Chat with your{' '}
            <span className="bg-gradient-to-r from-blue-500 to-indigo-600 text-transparent bg-clip-text">
              PDF documents
            </span>
          </h1>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            Upload your PDF and start chatting with its contents using AI. Get instant answers and insights from your documents.
          </p>
        </div>

        {/* Upload Card */}
        <Card
          variant="glass"
          {...getRootProps()}
          className={`
            cursor-pointer
            border-2 border-dashed
            ${isDragActive ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/10' : 'border-gray-200 dark:border-gray-800'}
            hover:border-blue-500 dark:hover:border-blue-500
            transition-colors
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center py-12 space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-full">
              {isUploading ? (
                <FileText className="w-8 h-8 text-blue-500" />
              ) : (
                <Upload className="w-8 h-8 text-blue-500" />
              )}
            </div>
            <div className="text-center space-y-2">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                {isDragActive
                  ? 'Drop your PDF here'
                  : isUploading
                  ? 'Uploading...'
                  : 'Drop your PDF or click to upload'}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Support for PDF files up to 10MB
              </p>
            </div>
            {isUploading && (
              <div className="w-full max-w-xs h-1 bg-gray-200 dark:bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        </Card>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            {
              title: 'Fast Processing',
              description: 'Upload your PDF and get instant access to its contents',
              icon: <ArrowRight className="w-5 h-5" />,
            },
            {
              title: 'AI-Powered Chat',
              description: 'Chat naturally with your documents using advanced AI',
              icon: <ArrowRight className="w-5 h-5" />,
            },
            {
              title: 'Source Citations',
              description: 'Get answers with references to the source content',
              icon: <ArrowRight className="w-5 h-5" />,
            },
          ].map((feature, index) => (
            <Card key={index} className="relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-indigo-600/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="relative space-y-2">
                <div className="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg w-fit">
                  {feature.icon}
                </div>
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {feature.description}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
