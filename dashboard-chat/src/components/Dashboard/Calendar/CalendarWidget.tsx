import React, { useEffect, useCallback, useState, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { RootState } from '../../../store';
import { setEvents, setLoading, setError } from '../../../store/slices/calendarSlice';
import { wsService } from '../../../services/websocket';
import { CALENDAR_COLORS, CALENDAR_NAMES } from '../../../config/secrets';

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
  const [minimizedEvents, setMinimizedEvents] = useState<Set<string>>(new Set());
  const [hiddenCalendars, setHiddenCalendars] = useState<Set<string>>(new Set());

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
    tomorrow.setDate(tomorrow.getDate() + 1);

    return filteredEvents.reduce(
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

  const formatEventTime = (startTime: string, endTime?: string): { date: string; time: string } => {
    const start = new Date(startTime);
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Format date
    let dateStr: string;
    if (start.toDateString() === now.toDateString()) {
      dateStr = `Today (${start.getDate()})`;
    } else if (start.toDateString() === tomorrow.toDateString()) {
      dateStr = `Tomorrow (${start.getDate()})`;
    } else {
      dateStr = start.toLocaleDateString('en-US', { 
        weekday: 'short', 
        month: 'short', 
        day: 'numeric' 
      });
    }

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

  const handleAddEvent = () => {
    wsService.sendMessage({
      type: 'calendar',
      action: 'request_add_event'
    });
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

  const renderEventItem = (event: CalendarEvent, isMinimized: boolean) => {
    const { date, time } = formatEventTime(event.startTime, event.endTime);
    const style = { '--calendar-color': getCalendarColor(event.calendar) } as React.CSSProperties;

    return (
      <div 
        key={event.id} 
        className={`event-item ${isMinimized ? 'minimized' : ''}`}
        style={style}
        onClick={() => toggleEventMinimized(event.id)}
      >
        <div className="event-datetime">
          <div className="event-date">{date}</div>
          <div className="event-time">{time}</div>
        </div>
        <div className="event-details">
          <div className="event-title">
            {event.title}
          </div>
          {!isMinimized && event.location && <div className="event-location">{event.location}</div>}
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
                groupedEvents.today.map(event => renderEventItem(event, minimizedEvents.has(event.id)))
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
                groupedEvents.upcoming.map(event => renderEventItem(event, minimizedEvents.has(event.id)))
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