/**
 * TemporalTimeline — visualises audit events on a time axis.
 *
 * Layout:
 *  Desktop (md+): horizontal scroll with nodes on a central line
 *  Mobile (<md):  vertical list with a left-side line and dot markers
 */

'use client';

import React, { useState } from 'react';
import type { TimelineEvent } from '@/lib/types/api';

interface TemporalTimelineProps {
  events: TimelineEvent[];
}

const SEVERITY_COLORS: Record<string, { dot: string; text: string; bg: string }> = {
  critical: { dot: 'bg-red-500', text: 'text-red-700', bg: 'bg-red-50' },
  high:     { dot: 'bg-orange-500', text: 'text-orange-700', bg: 'bg-orange-50' },
  medium:   { dot: 'bg-yellow-500', text: 'text-yellow-700', bg: 'bg-yellow-50' },
  low:      { dot: 'bg-blue-400', text: 'text-blue-700', bg: 'bg-blue-50' },
  document: { dot: 'bg-gray-400', text: 'text-gray-700', bg: 'bg-gray-50' },
  milestone:{ dot: 'bg-green-500', text: 'text-green-700', bg: 'bg-green-50' },
};

function colorFor(event: TimelineEvent) {
  if (event.category === 'document') return SEVERITY_COLORS.document;
  if (event.category === 'milestone') return SEVERITY_COLORS.milestone;
  return SEVERITY_COLORS[event.severity ?? 'low'] ?? SEVERITY_COLORS.low;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return iso.slice(0, 10);
  }
}

// ---------------------------------------------------------------------------
// Single event node
// ---------------------------------------------------------------------------

function EventNode({
  event,
  expanded,
  onToggle,
}: {
  event: TimelineEvent;
  expanded: boolean;
  onToggle: () => void;
}) {
  const colors = colorFor(event);

  return (
    <div className="relative pl-8">
      {/* Dot */}
      <span
        className={`absolute left-0 top-1.5 w-4 h-4 rounded-full border-2 border-white shadow ${colors.dot}`}
        aria-hidden="true"
      />

      <button
        onClick={onToggle}
        className={`w-full text-left rounded-lg p-3 transition-colors ${
          expanded ? colors.bg : 'hover:bg-gray-50'
        }`}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-xs text-gray-500 mb-0.5">{formatDate(event.date)}</p>
            <p className={`text-sm font-medium ${colors.text}`}>{event.label}</p>
          </div>
          <span className="text-gray-400 text-xs flex-shrink-0 mt-1">
            {expanded ? '▲' : '▼'}
          </span>
        </div>
      </button>

      {expanded && (
        <div className="ml-0 mt-1 mb-3 px-3 py-2 bg-white border border-gray-100 rounded-lg text-sm text-gray-700">
          <p>{event.description}</p>
          {event.document_id && (
            <p className="mt-1 text-xs text-gray-400 font-mono">{event.document_id}</p>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Desktop horizontal timeline (md+)
// ---------------------------------------------------------------------------

function HorizontalTimeline({
  events,
  expandedId,
  onToggle,
}: {
  events: TimelineEvent[];
  expandedId: string | null;
  onToggle: (id: string) => void;
}) {
  return (
    <div className="relative overflow-x-auto pb-4">
      {/* Horizontal line */}
      <div className="absolute top-8 left-0 right-0 h-0.5 bg-gray-200" aria-hidden="true" />

      <div className="flex gap-0 min-w-max">
        {events.map((event) => {
          const colors = colorFor(event);
          const expanded = expandedId === event.id;
          return (
            <div key={event.id} className="flex flex-col items-center w-44 relative">
              {/* Dot on line */}
              <button
                onClick={() => onToggle(event.id)}
                className={`
                  relative z-10 w-5 h-5 rounded-full border-2 border-white shadow mt-6 mb-2
                  transition-transform hover:scale-110 focus:outline-none
                  ${colors.dot}
                `}
                aria-label={`${event.label} — ${formatDate(event.date)}`}
              />

              {/* Card below dot */}
              <button
                onClick={() => onToggle(event.id)}
                className={`
                  w-40 rounded-lg p-2 text-left transition-colors border
                  ${expanded
                    ? `${colors.bg} border-current ${colors.text}`
                    : 'bg-white border-gray-100 hover:border-gray-200'
                  }
                `}
              >
                <p className="text-xs text-gray-400">{formatDate(event.date)}</p>
                <p className={`text-xs font-medium leading-snug mt-0.5 ${colors.text}`}>
                  {event.label}
                </p>
              </button>

              {/* Expanded detail (floats below) */}
              {expanded && (
                <div className="absolute top-full mt-1 left-0 w-56 z-20 bg-white border border-gray-200 rounded-lg p-3 shadow-lg text-xs text-gray-700">
                  <p>{event.description}</p>
                  {event.document_id && (
                    <p className="mt-1 text-gray-400 font-mono">{event.document_id}</p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function TemporalTimeline({ events }: TemporalTimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const toggle = (id: string) => setExpandedId((prev) => (prev === id ? null : id));

  if (events.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No timeline events to display.
      </div>
    );
  }

  const sorted = [...events].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
  );

  return (
    <div>
      {/* Mobile: vertical */}
      <div className="md:hidden relative">
        {/* Vertical line */}
        <div className="absolute left-2 top-0 bottom-0 w-0.5 bg-gray-200" aria-hidden="true" />
        <div className="space-y-1">
          {sorted.map((event) => (
            <EventNode
              key={event.id}
              event={event}
              expanded={expandedId === event.id}
              onToggle={() => toggle(event.id)}
            />
          ))}
        </div>
      </div>

      {/* Desktop: horizontal */}
      <div className="hidden md:block">
        <HorizontalTimeline events={sorted} expandedId={expandedId} onToggle={toggle} />
      </div>
    </div>
  );
}
