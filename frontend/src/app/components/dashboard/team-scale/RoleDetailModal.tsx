import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../../../ui/dialog';
import { Badge } from '../../../ui/badge';
import { Button } from '../../../ui/button';
import { ArrowRight } from 'lucide-react';
import { getRoleResponsibilities } from './utils';

interface RoleDetailModalProps {
  selectedRole: any;
  isOpen: boolean;
  onClose: () => void;
}

export function RoleDetailModal({ selectedRole, isOpen, onClose }: RoleDetailModalProps) {
  if (!selectedRole) return null;

  const responsibilities = getRoleResponsibilities(selectedRole.role);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{selectedRole.role}</DialogTitle>
          <DialogDescription>
            Detailed hiring requirements for {selectedRole.stage}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-2">Hiring Details</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Positions:</span>
                  <Badge>{selectedRole.count}x</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Urgency:</span>
                  <Badge variant={selectedRole.urgency === 'critical' ? 'destructive' : 'default'}>
                    {selectedRole.urgency}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Timeline:</span>
                  <span>2-3 months</span>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Required Skills</h4>
              <div className="flex flex-wrap gap-1">
                {selectedRole.skills?.map((skill: string, index: number) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Key Responsibilities</h4>
            <ul className="text-sm space-y-1 text-muted-foreground">
              {responsibilities.map((responsibility, index) => (
                <li key={index}>{responsibility}</li>
              ))}
            </ul>
          </div>

          <Button className="w-full">
            Start Recruiting Process
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}