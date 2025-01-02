import React, { useEffect, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { RootState } from '../../../store';
import { setEvents, setLoading, setError } from '../../../store/slices/calendarSlice';
import { wsService } from '../../../services/websocket';

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
  upcoming: CalendarEvent[];
}

export const CalendarWidget: React.FC = () => {
  const dispatch = useAppDispatch();
  const { events, isLoading, error } = useAppSelector((state: RootState) => state.calendar);

  const fetchEvents = useCallback(async () => {
    try {
      dispatch(setLoading(true));
      const response = await fetch('http://localhost:8000/calendar/events');
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

  const groupEvents = (events: CalendarEvent[]): GroupedEvents => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    return events.reduce(
      (groups, event) => {
        const eventDate = new Date(event.startTime);
        if (eventDate >= today && eventDate < tomorrow) {
          groups.today.push(event);
        } else if (eventDate >= tomorrow) {
          groups.upcoming.push(event);
        }
        return groups;
      },
      { today: [], upcoming: [] } as GroupedEvents
    );
  };

  const formatEventTime = (startTime: string, endTime?: string): string => {
    const start = new Date(startTime);
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
      return `${timeStr} - ${endTimeStr}`;
    }
    
    return timeStr;
  };

  const handleRefresh = () => {
    fetchEvents();
  };

  const handleAddEvent = () => {
    wsService.sendMessage({
      type: 'calendar',
      action: 'request_add_event'
    });
  };

  const groupedEvents = groupEvents(events);

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
                groupedEvents.today.map(event => (
                  <div key={event.id} className="event-item">
                    <div className="event-time">{formatEventTime(event.startTime, event.endTime)}</div>
                    <div className="event-title">{event.title}</div>
                    {event.location && <div className="event-location">{event.location}</div>}
                  </div>
                ))
              ) : (
                <div className="no-events">No events today</div>
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
                groupedEvents.upcoming.map(event => (
                  <div key={event.id} className="event-item">
                    <div className="event-time">{formatEventTime(event.startTime, event.endTime)}</div>
                    <div className="event-title">{event.title}</div>
                    {event.location && <div className="event-location">{event.location}</div>}
                  </div>
                ))
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