import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { RootState } from '../../../store';
import { setEvents, setLoading, setError } from '../../../store/slices/calendarSlice';
import { wsService } from '../../../services/websocket';
import { CALENDAR_COLORS, CALENDAR_NAMES, GOOGLE_MAPS_API_KEY } from '../../../config/secrets';

interface CalendarEvent {
  id: string;
  title: string;
  startTime: string;
  endTime?: string;
  location?: string;
  description?: string;
  calendar: string;
}

interface GroupedEvents {
  today: CalendarEvent[];
  fortnite: CalendarEvent[];
  upcoming: CalendarEvent[];
}

interface Props {
  onAddEvent: (message: string) => void;
}

const CalendarWidget: React.FC<Props> = ({ onAddEvent }) => {
  const dispatch = useAppDispatch();
  const { events, isLoading, error } = useAppSelector((state: RootState) => state.calendar);
  const [minimizedEvents, setMinimizedEvents] = useState<Set<string>>(new Set());
  const [hiddenCalendars, setHiddenCalendars] = useState<Set<string>>(new Set());
  const [expandedLocations, setExpandedLocations] = useState<Set<string>>(new Set());

  const fetchEvents = useCallback(async () => {
    try {
      dispatch(setLoading(true));
      const response = await fetch('http://localhost:8000/calendar/events?max_results=30');
      if (!response.ok) {
        throw new Error('Failed to fetch calendar events');
      }
      const data = await response.json();
      dispatch(setEvents(data));
    } catch (err) {
      dispatch(setError(err instanceof Error ? err.message : 'Failed to fetch events'));
    }
  }, [dispatch]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  // Add debug log for calendar names
  useEffect(() => {
    if (events.length > 0) {
      console.log('Calendar names:', [...new Set(events.map(event => event.calendar))]);
    }
  }, [events]);

  const toggleCalendar = (calendarName: string) => {
    setHiddenCalendars(prev => {
      const newSet = new Set(prev);
      if (newSet.has(calendarName)) {
        newSet.delete(calendarName);
      } else {
        newSet.add(calendarName);
      }
      return newSet;
    });
  };

  const getFilteredEvents = (events: CalendarEvent[]) => {
    return events.filter(event => !hiddenCalendars.has(event.calendar));
  };

  const groupEvents = (events: CalendarEvent[]): GroupedEvents => {
    const filteredEvents = getFilteredEvents(events);
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    const fortnite = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    fortnite.setDate(tomorrow.getDate() + 2);

    return filteredEvents.reduce(
      (groups, event) => {
        const eventDate = new Date(event.startTime);
        if (eventDate >= today && eventDate < tomorrow) {
          groups.today.push(event);
        } else if (eventDate >= tomorrow && eventDate < fortnite) {
            groups.fortnite.push(event);
        } else if (eventDate >= fortnite) {
          groups.upcoming.push(event);
        }
        return groups;
      },
      { today: [], fortnite: [], upcoming: [] } as GroupedEvents
    );
  };

  const formatEventTime = (startTime: string, endTime?: string): { date: string; time: string } => {
    const start = new Date(startTime);
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Format date
    let dateStr: string;
    dateStr = start.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric' 
    });

    // Format time
    const timeStr = start.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
    
    if (endTime) {
      const end = new Date(endTime);
      const endTimeStr = end.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
      return {
        date: dateStr,
        time: `${timeStr} - ${endTimeStr}`
      };
    }
    
    return {
      date: dateStr,
      time: timeStr
    };
  };

  const handleRefresh = () => {
    fetchEvents();
  };

  const handleAddEvent = async () => {
    const button = document.querySelector('.widget-button') as HTMLButtonElement;
    if (!button) return;

    button.disabled = true;
    button.innerHTML = `
      <svg class="loading-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="12" height="12">
        <circle cx="12" cy="12" r="10" />
      </svg>
      Adding...
    `;

    try {
      // Show immediate feedback in chat
      onAddEvent("I'll help you add a calendar event. Please describe the event in plain language, including when it should occur. For example:\n- 'Team meeting tomorrow at 2pm for 1 hour'\n- 'Lunch with John next Thursday at noon at Cafe Luigi'\n- 'Weekly standup every Monday at 9am'");

      // Send command to backend
      const response = await fetch('http://localhost:8000/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: '/calendar add'
        })
      });

      if (!response.ok) {
        throw new Error('Failed to initiate event creation');
      }
    } catch (err) {
      console.error("Error initiating event creation:", err);
      onAddEvent("Sorry, I encountered an error while trying to add the event. Please try again.");
    } finally {
      // Reset button state
      button.disabled = false;
      button.innerHTML = `Add Event`;
    }
  };

  const toggleEventMinimized = (eventId: string) => {
    setMinimizedEvents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };

  const handleLocationClick = (e: React.MouseEvent, eventId: string, location: string) => {
    e.stopPropagation();
    setExpandedLocations(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };

  const renderEvent = (event: CalendarEvent) => {
    const isMinimized = minimizedEvents.has(event.id);
    const isLocationExpanded = expandedLocations.has(event.id);
    const eventDate = new Date(event.startTime);
    const endDate = event.endTime ? new Date(event.endTime) : null;

    return (
      <div
        key={event.id}
        className={`event-item ${isMinimized ? 'minimized' : ''}`}
        style={{ '--calendar-color': getCalendarColor(event.calendar) } as React.CSSProperties}
        onClick={() => handleEventClick(event.id)}
      >
        <div className="event-datetime">
          <span className="event-date">{formatDate(eventDate)}</span>
          <span className="event-time">{formatTime(eventDate)}{endDate && ` - ${formatTime(endDate)}`}</span>
        </div>
        <div className="event-details">
          <div className="event-title">{event.title}</div>
          {event.location && (
            <div className="event-location-container">
              <div 
                className="event-location"
                onClick={(e) => handleLocationClick(e, event.id, event.location!)}
              >
                {event.location}
              </div>
              {isLocationExpanded && (
                <div className="event-map">
                  <iframe
                    title={`Map for ${event.title}`}
                    width="100%"
                    height="200"
                    style={{ border: 0 }}
                    loading="lazy"
                    allowFullScreen
                    referrerPolicy="no-referrer-when-downgrade"
                    src={`https://www.google.com/maps/embed/v1/place?key=${GOOGLE_MAPS_API_KEY}&q=${encodeURIComponent(event.location)}`}
                  ></iframe>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const getShortCalendarName = (calendar: string) => {
    return calendar.split(' ')[0];
  };

  const renderCalendarToggles = () => {
    const uniqueCalendars = [...new Set(events.map(event => event.calendar))];
    return (
      <div className="calendar-toggles">
        {uniqueCalendars.map(calendar => (
          <button
            key={calendar}
            className={`calendar-toggle ${hiddenCalendars.has(calendar) ? 'disabled' : ''}`}
            style={{ backgroundColor: getCalendarColor(calendar) }}
            onClick={() => toggleCalendar(calendar)}
            title={calendar}
          >
            <span className="calendar-toggle-dot"></span>
            {getShortCalendarName(calendar)}
          </button>
        ))}
      </div>
    );
  };

  const groupedEvents = groupEvents(events);

  // Add a function to get calendar color
  const getCalendarColor = (calendarName: string) => {
    return CALENDAR_COLORS[calendarName as keyof typeof CALENDAR_COLORS] || '#007bff';
  };

  const formatDate = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const handleEventClick = (eventId: string) => {
    setMinimizedEvents(prev => {
      const newSet = new Set(prev);
      if (newSet.has(eventId)) {
        newSet.delete(eventId);
      } else {
        newSet.add(eventId);
      }
      return newSet;
    });
  };

  return (
    <div className="widget calendar-widget">
      <div className="widget-header">
        <h2>🗓️ Calendar</h2>
        <div className="widget-actions">
          <button className="widget-button" onClick={handleAddEvent}>
            Add Event
          </button>
          <button className="widget-button" onClick={handleRefresh}>
            Refresh
          </button>
        </div>
      </div>
      {renderCalendarToggles()}
      <div className="widget-content">
        {error && <div className="error-message">{error}</div>}
        <div className="calendar-events">
          <div className="event-group">
            <h3>Today</h3>
            <div className="event-list">
              {isLoading ? (
                <div className="event-item skeleton-loading">
                  <div className="event-time"></div>
                  <div className="event-title"></div>
                </div>
              ) : groupedEvents.today.length > 0 ? (
                groupedEvents.today.map(event => renderEvent(event))
              ) : (
                <div className="no-events">No events today</div>
              )}
            </div>
          </div>
          <div className="event-group">
            <h3>Tomorrow</h3>
            <div className="event-list">
              {isLoading ? (
                <div className="event-item skeleton-loading">
                  <div className="event-time"></div>
                  <div className="event-title"></div>
                </div>
              ) : groupedEvents.fortnite.length > 0 ? (
                groupedEvents.fortnite.map(event => renderEvent(event))
              ) : (
                <div className="no-events">No events tomorrow</div>
              )}
            </div>
          </div>
          <div className="event-group">
            <h3>Upcoming</h3>
            <div className="event-list">
              {isLoading ? (
                <div className="event-item skeleton-loading">
                  <div className="event-time"></div>
                  <div className="event-title"></div>
                </div>
              ) : groupedEvents.upcoming.length > 0 ? (
                groupedEvents.upcoming.map(event => renderEvent(event))
              ) : (
                <div className="no-events">No upcoming events</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalendarWidget; 