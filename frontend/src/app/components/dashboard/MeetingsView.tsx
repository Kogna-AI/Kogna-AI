import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/badge';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Textarea } from '../../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Checkbox } from '../../ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../../ui/dialog';
import { Calendar, Clock, Users, Video, Bot, UserPlus, Zap } from 'lucide-react';

const upcomingMeetings = [
  { 
    id: 0, 
    title: 'Meeting with Kognii', 
    subtitle: 'Competitor analysis, emerging tech companies',
    time: '9:00 AM', 
    attendees: 1, 
    type: 'ai-strategy',
    isKogniiMeeting: true 
  },
  { id: 1, title: 'Q2 Strategic Review', time: '10:00 AM', attendees: 8, type: 'strategic' },
  { id: 2, title: 'Product Roadmap Discussion', time: '2:00 PM', attendees: 5, type: 'product' },
  { id: 3, title: 'Team Performance Review', time: '4:00 PM', attendees: 12, type: 'team' }
];

const teamMembers = [
  { id: 'sarah', name: 'Sarah Chen', role: 'Product Manager', available: true },
  { id: 'marcus', name: 'Marcus Rodriguez', role: 'Engineering Lead', available: true },
  { id: 'elena', name: 'Elena Vasquez', role: 'UX Designer', available: false },
  { id: 'david', name: 'David Kim', role: 'Data Analyst', available: true },
  { id: 'priya', name: 'Priya Patel', role: 'Marketing Director', available: true },
  { id: 'james', name: 'James Wilson', role: 'Sales Lead', available: true }
];

interface MeetingFormData {
  title: string;
  description: string;
  date: string;
  time: string;
  duration: string;
  type: string;
  attendees: string[];
  includeKognii: boolean;
}

function MeetingSchedulingDialog() {
  const [isOpen, setIsOpen] = useState(false);
  const [meetingData, setMeetingData] = useState<MeetingFormData>({
    title: '',
    description: '',
    date: '',
    time: '',
    duration: '30',
    type: 'general',
    attendees: [],
    includeKognii: false
  });

  const handlePresetSelection = (preset: 'kognii-1on1' | 'team-with-kognii') => {
    if (preset === 'kognii-1on1') {
      setMeetingData({
        ...meetingData,
        title: '1:1 Strategy Session with Kognii',
        description: 'Personal strategy discussion and AI insights',
        type: 'ai-strategy',
        attendees: [],
        includeKognii: true
      });
    } else {
      setMeetingData({
        ...meetingData,
        title: 'Team Strategy Meeting',
        description: 'Team meeting with AI strategic insights from Kognii',
        type: 'strategic',
        includeKognii: true
      });
    }
  };

  const handleAttendeeToggle = (memberId: string) => {
    setMeetingData(prev => ({
      ...prev,
      attendees: prev.attendees.includes(memberId)
        ? prev.attendees.filter(id => id !== memberId)
        : [...prev.attendees, memberId]
    }));
  };

  const handleSubmit = () => {
    // Here you would typically save the meeting to your backend
    console.log('Meeting scheduled:', meetingData);
    setIsOpen(false);
    // Reset form
    setMeetingData({
      title: '',
      description: '',
      date: '',
      time: '',
      duration: '30',
      type: 'general',
      attendees: [],
      includeKognii: false
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Calendar className="w-4 h-4" />
          Schedule Meeting
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Schedule New Meeting</DialogTitle>
          <DialogDescription>
            Create a new meeting and collaborate with your team and Kognii AI
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Meeting Presets */}
          <div className="space-y-3">
            <Label>Quick Setup</Label>
            <div className="grid grid-cols-2 gap-3">
              <Button
                type="button"
                variant="outline"
                className="h-auto p-4 flex flex-col items-start gap-2"
                onClick={() => handlePresetSelection('kognii-1on1')}
              >
                <div className="flex items-center gap-2">
                  <Bot className="w-4 h-4 text-blue-600" />
                  <span>1:1 with Kognii</span>
                </div>
                <p className="text-xs text-muted-foreground text-left">
                  Personal strategy session with AI insights
                </p>
              </Button>
              <Button
                type="button"
                variant="outline"
                className="h-auto p-4 flex flex-col items-start gap-2"
                onClick={() => handlePresetSelection('team-with-kognii')}
              >
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-green-600" />
                  <span>Team + Kognii</span>
                </div>
                <p className="text-xs text-muted-foreground text-left">
                  Team meeting with AI strategic partner
                </p>
              </Button>
            </div>
          </div>

          {/* Meeting Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label htmlFor="title">Meeting Title</Label>
              <Input
                id="title"
                value={meetingData.title}
                onChange={(e) => setMeetingData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Enter meeting title"
              />
            </div>

            <div className="col-span-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={meetingData.description}
                onChange={(e) => setMeetingData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Meeting agenda and objectives"
                rows={3}
              />
            </div>

            <div>
              <Label htmlFor="date">Date</Label>
              <Input
                id="date"
                type="date"
                value={meetingData.date}
                onChange={(e) => setMeetingData(prev => ({ ...prev, date: e.target.value }))}
              />
            </div>

            <div>
              <Label htmlFor="time">Time</Label>
              <Input
                id="time"
                type="time"
                value={meetingData.time}
                onChange={(e) => setMeetingData(prev => ({ ...prev, time: e.target.value }))}
              />
            </div>

            <div>
              <Label htmlFor="duration">Duration (minutes)</Label>
              <Select value={meetingData.duration} onValueChange={(value) => setMeetingData(prev => ({ ...prev, duration: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="45">45 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="90">1.5 hours</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="type">Meeting Type</Label>
              <Select value={meetingData.type} onValueChange={(value) => setMeetingData(prev => ({ ...prev, type: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">General</SelectItem>
                  <SelectItem value="strategic">Strategic</SelectItem>
                  <SelectItem value="ai-strategy">AI Strategy</SelectItem>
                  <SelectItem value="product">Product</SelectItem>
                  <SelectItem value="team">Team</SelectItem>
                  <SelectItem value="review">Review</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Include Kognii */}
          <div className="flex items-center space-x-2">
            <Checkbox
              id="includeKognii"
              checked={meetingData.includeKognii}
              onCheckedChange={(checked) => setMeetingData(prev => ({ ...prev, includeKognii: !!checked }))}
            />
            <Label htmlFor="includeKognii" className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-600" />
              Include Kognii as strategic partner
            </Label>
          </div>

          {/* Team Members */}
          <div className="space-y-3">
            <Label>Team Members</Label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {teamMembers.map((member) => (
                <div key={member.id} className="flex items-center space-x-2 p-2 border rounded">
                  <Checkbox
                    id={member.id}
                    checked={meetingData.attendees.includes(member.id)}
                    onCheckedChange={() => handleAttendeeToggle(member.id)}
                    disabled={!member.available}
                  />
                  <div className="flex-1 min-w-0">
                    <Label 
                      htmlFor={member.id} 
                      className={`text-sm ${!member.available ? 'text-muted-foreground' : ''}`}
                    >
                      {member.name}
                    </Label>
                    <p className="text-xs text-muted-foreground">{member.role}</p>
                  </div>
                  {!member.available && (
                    <Badge variant="secondary" className="text-xs">Busy</Badge>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button 
              type="button" 
              onClick={handleSubmit}
              disabled={!meetingData.title || !meetingData.date || !meetingData.time}
            >
              Schedule Meeting
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function MeetingsView() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1>Meetings</h1>
          <p className="text-muted-foreground">Schedule and manage strategic meetings</p>
        </div>
        <MeetingSchedulingDialog />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Today's Meetings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {upcomingMeetings.map((meeting) => (
              <div key={meeting.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center gap-3">
                  {meeting.isKogniiMeeting ? (
                    <Bot className="w-4 h-4 text-blue-600" />
                  ) : (
                    <Calendar className="w-4 h-4 text-blue-600" />
                  )}
                  <div>
                    <h4 className="font-medium">{meeting.title}</h4>
                    <p className="text-sm text-muted-foreground">
                      {meeting.subtitle && `${meeting.subtitle} • `}
                      {meeting.time} • {meeting.attendees} {meeting.attendees === 1 ? 'attendee' : 'attendees'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className={meeting.isKogniiMeeting ? 'border-blue-600 text-blue-600' : ''}>
                    {meeting.type}
                  </Badge>
                  <Button variant="outline" size="sm">
                    <Video className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}