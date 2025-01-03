import React, { useState, useEffect, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { setEmails, setLoading, setError, markEmailAsRead, toggleEmailStar } from '../../../store/slices/emailSlice';
import { RootState } from '../../../store/store';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface Email {
  id: string;
  from: string;
  subject: string;
  date: string;
  snippet: string;
  body?: string;
  labels: string[];
}

interface Props {
  onDraftReply: (emailId: string) => void;
}

const EmailWidget: React.FC<Props> = ({ onDraftReply }) => {
  const dispatch = useDispatch();
  const { emails, loading, error } = useSelector((state: RootState) => state.email);
  const [minimizedEmails, setMinimizedEmails] = useState<Set<string>>(new Set());
  const [expandedEmailId, setExpandedEmailId] = useState<string | null>(null);
  const [showUnread, setShowUnread] = useState(true);
  const [showStarred, setShowStarred] = useState(true);
  const [showRead, setShowRead] = useState(true);
  const [starredEmails, setStarredEmails] = useState<Email[]>([]);
  const [loadingStarred, setLoadingStarred] = useState(false);

  const fetchEmails = async () => {
    try {
      dispatch(setLoading(true));
      const response = await fetch('http://localhost:8000/api/emails/recent');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      dispatch(setEmails(data.emails));
      dispatch(setError(null));
    } catch (err) {
      console.error("Error fetching emails:", err);
      dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch emails'));
    } finally {
      dispatch(setLoading(false));
    }
  };

  const fetchStarredEmails = async () => {
    try {
      setLoadingStarred(true);
      const response = await fetch('http://localhost:8000/api/emails/starred?max_results=10');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      // Map over starred emails and fetch their content
      const starredWithContent = await Promise.all(
        data.emails.map(async (email: Email) => {
          try {
            const contentResponse = await fetch(`http://localhost:8000/api/emails/${email.id}/content`, {
              method: 'GET',
              headers: {
                'Accept': 'text/html',
              },
            });
            if (contentResponse.ok) {
              const contentData = await contentResponse.json();
              return {
                ...email,
                body: contentData.html || contentData.body
              };
            }
            return email;
          } catch (err) {
            console.error(`Error fetching content for email ${email.id}:`, err);
            return email;
          }
        })
      );
      
      setStarredEmails(starredWithContent);
    } catch (err) {
      console.error("Error fetching starred emails:", err);
    } finally {
      setLoadingStarred(false);
    }
  };

  useEffect(() => {
    fetchEmails();
    fetchStarredEmails();
  }, []);

  // Filter and sort emails by category
  const filteredAndSortedEmails = useMemo(() => {
    // Create a map of starred email IDs for quick lookup
    const starredEmailIds = new Set(starredEmails.map(email => email.id));
    
    // Combine recent emails and starred emails, ensuring starred status is preserved
    const allEmails = emails.map(email => {
      // If this email is in our starred set, make sure it has the STARRED label
      if (starredEmailIds.has(email.id) && !email.labels.includes('STARRED')) {
        return {
          ...email,
          labels: [...email.labels, 'STARRED']
        };
      }
      return email;
    });

    // Add any starred emails that aren't in the recent list
    starredEmails.forEach(starredEmail => {
      if (!allEmails.some(email => email.id === starredEmail.id)) {
        allEmails.push(starredEmail);
      }
    });

    return allEmails.filter(email => {
      const isUnread = email.labels?.includes('UNREAD');
      const isStarred = email.labels?.includes('STARRED');
      
      if (isUnread) return showUnread;
      if (isStarred) return showStarred;
      return showRead;
    }).sort((a, b) => {
      // First sort by unread status (unread first)
      if (a.labels?.includes('UNREAD') && !b.labels?.includes('UNREAD')) return -1;
      if (!a.labels?.includes('UNREAD') && b.labels?.includes('UNREAD')) return 1;
      
      // Then sort by starred status (starred first)
      if (a.labels?.includes('STARRED') && !b.labels?.includes('STARRED')) return -1;
      if (!a.labels?.includes('STARRED') && b.labels?.includes('STARRED')) return 1;
      
      // If both have same status, sort by date (newer first)
      return new Date(b.date).getTime() - new Date(a.date).getTime();
    });
  }, [emails, starredEmails, showUnread, showStarred, showRead]);

  const handleMarkAsRead = async (e: React.MouseEvent, emailId: string) => {
    e.stopPropagation();
    try {
      dispatch(markEmailAsRead(emailId));
      const response = await fetch(`http://localhost:8000/api/emails/${emailId}/mark-read`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (err) {
      console.error("Error marking email as read:", err);
      fetchEmails();
    }
  };

  const handleToggleStar = async (e: React.MouseEvent, emailId: string, isStarred: boolean) => {
    e.stopPropagation();
    try {
      // Optimistically update the UI
      dispatch(toggleEmailStar(emailId));
      
      // Make the API call in the background
      const response = await fetch(`http://localhost:8000/api/emails/${emailId}/${isStarred ? 'unstar' : 'star'}`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (err) {
      console.error("Error toggling star:", err);
      // If there was an error, revert the optimistic update
      dispatch(toggleEmailStar(emailId));
    }
  };

  const handleDraftReply = async (e: React.MouseEvent, emailId: string) => {
    e.stopPropagation();
    
    // Get the button element
    const button = e.currentTarget as HTMLButtonElement;
    button.disabled = true;
    button.innerHTML = `
      <svg class="loading-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
        <circle cx="12" cy="12" r="10" />
      </svg>
      Drafting...
    `;

    try {
      // Show immediate feedback in chat
      onDraftReply("I'm drafting a reply to this email...");

      // Expand the email if it's not already expanded
      setExpandedEmailId(emailId);

      // Get the email content without marking as read
      const readResponse = await fetch('http://localhost:8000/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Use a special command that doesn't mark as read
          command: `/email read ${emailId} keep-unread`
        })
      });

      if (!readResponse.ok) {
        throw new Error('Failed to read email');
      }

      // Then trigger draft reply
      const draftResponse = await fetch('http://localhost:8000/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: '/email draft reply'
        })
      });

      if (!draftResponse.ok) {
        throw new Error('Failed to create draft');
      }

      const draftData = await draftResponse.json();
      // Pass the draft response to the chat component
      onDraftReply(draftData.data);
    } catch (err) {
      console.error("Error preparing draft reply:", err);
      onDraftReply("Sorry, I encountered an error while drafting the reply. Please try again.");
    } finally {
      // Reset button state
      button.disabled = false;
      button.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
          <path d="M3 10h18M3 14h18" />
        </svg>
        Draft Reply
      `;
    }
  };

  const handleEmailClick = async (emailId: string) => {
    // If we're closing the email, just close it
    if (expandedEmailId === emailId) {
      setExpandedEmailId(null);
      return;
    }

    // Otherwise, fetch the full email content
    try {
      const response = await fetch(`http://localhost:8000/api/emails/${emailId}/content`, {
        method: 'GET',
        headers: {
          'Accept': 'text/html',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch email content');
      }

      const data = await response.json();
      
      // Update the email in our list with the full body
      const updatedEmails = emails.map(email => {
        if (email.id === emailId) {
          return {
            ...email,
            body: data.html || data.body // Use HTML content if available, fall back to plain text
          };
        }
        return email;
      });
      dispatch(setEmails(updatedEmails));
      setExpandedEmailId(emailId);
    } catch (err) {
      console.error("Error fetching email content:", err);
      // Still expand the email to show the snippet if full content fetch fails
      setExpandedEmailId(emailId);
    }
  };

  const handleOpenInGmail = (emailId: string) => {
    window.open(`https://mail.google.com/mail/u/0/#inbox/${emailId}`, '_blank');
  };

  const processHtmlContent = (html: string): string => {
    // Create a temporary div to parse the HTML
    const div = document.createElement('div');
    div.innerHTML = html;
    
    // Find all links and add target="_blank" and rel="noopener noreferrer"
    const links = div.getElementsByTagName('a');
    for (let i = 0; i < links.length; i++) {
      const link = links[i];
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      
      // Check if this is a YouTube link
      const url = link.href;
      const youtubeRegex = /(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
      const match = url.match(youtubeRegex);
      
      if (match && match[1]) {
        const videoId = match[1];
        // Create an iframe for the YouTube embed
        const iframe = document.createElement('div');
        iframe.innerHTML = `
          <div class="youtube-embed">
            <iframe 
              width="560" 
              height="315" 
              src="https://www.youtube.com/embed/${videoId}" 
              frameborder="0" 
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
              allowfullscreen
            ></iframe>
          </div>
        `;
        // Replace the link with the iframe
        link.parentNode?.insertBefore(iframe.firstElementChild!, link);
        link.remove();
      }
    }
    
    return div.innerHTML;
  };

  const renderEmailItem = (email: Email) => {
    const isExpanded = expandedEmailId === email.id;
    const fromName = email.from.split('<')[0].trim();
    const fromEmail = email.from.match(/<(.+?)>/)?.[1] || '';
    const isUnread = email.labels?.includes('UNREAD');
    const isStarred = email.labels?.includes('STARRED');

    return (
      <div
        key={email.id}
        className={`email-item ${isUnread ? 'unread' : ''} ${isExpanded ? 'expanded' : ''} ${isStarred ? 'starred' : ''}`}
        onClick={() => handleEmailClick(email.id)}
      >
        <div className="email-content">
          <div className="email-header">
            <div className="email-from">{fromName}</div>
          </div>
          <div className="email-subject">{email.subject}</div>
        </div>
        <div className="email-actions">
          {isUnread && (
            <>
              <button 
                className="mark-read-button"
                onClick={(e) => handleMarkAsRead(e, email.id)}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                  <path d="M20 6L9 17l-5-5" />
                </svg>
                Mark as read
              </button>
              <button 
                className="draft-reply-button"
                onClick={(e) => handleDraftReply(e, email.id)}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
                  <path d="M3 10h18M3 14h18" />
                </svg>
                Draft Reply
              </button>
            </>
          )}
          <button 
            className={`star-button ${isStarred ? 'starred' : ''}`}
            onClick={(e) => handleToggleStar(e, email.id, isStarred)}
          >
            <svg viewBox="0 0 24 24" fill={isStarred ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" width="12" height="12">
              <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
            </svg>
            {isStarred ? 'Unstar' : 'Star'}
          </button>
        </div>
        {isExpanded && (
          <div className="email-expanded-content">
            <div className="email-details">
              <div className="email-from-full">
                <strong>From:</strong> {fromName} {fromEmail && `<${fromEmail}>`}
              </div>
              <div className="email-body">
                {email.body ? (
                  <div 
                    dangerouslySetInnerHTML={{ __html: processHtmlContent(email.body) }} 
                    className="email-body-content"
                  />
                ) : (
                  <div className="email-loading">Loading email content...</div>
                )}
              </div>
            </div>
            <div className="email-actions">
              <button 
                className="open-gmail-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleOpenInGmail(email.id);
                }}
              >
                Open in Gmail
              </button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="widget email-widget">
      <div className="widget-header">
        <h2>📧 Emails</h2>
        <button onClick={() => { fetchEmails(); fetchStarredEmails(); }} className="refresh-button">
          Refresh
        </button>
      </div>
      <div className="email-toggles">
        <button 
          className={`email-toggle ${showUnread ? 'active' : ''}`}
          onClick={() => setShowUnread(!showUnread)}
        >
          📬 Unread
        </button>
        <button 
          className={`email-toggle ${showStarred ? 'active' : ''}`}
          onClick={() => setShowStarred(!showStarred)}
        >
          ⭐️ Starred
        </button>
        <button 
          className={`email-toggle ${showRead ? 'active' : ''}`}
          onClick={() => setShowRead(!showRead)}
        >
          📫 Read
        </button>
      </div>
      <div className="widget-content">
        {loading && <div className="loading">Loading emails...</div>}
        {error && <div className="error">{error}</div>}
        {!loading && !error && emails.length === 0 && (
          <div className="no-emails">No emails found</div>
        )}
        {!loading && !error && emails.length > 0 && (
          <div className="email-list">
            {filteredAndSortedEmails.map(renderEmailItem)}
          </div>
        )}
      </div>
    </div>
  );
};

export default EmailWidget; 