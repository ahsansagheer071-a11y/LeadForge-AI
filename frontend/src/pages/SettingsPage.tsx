import { Save } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Input, Label } from '@/components/Input';
import { Button } from '@/components/Button';

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold tracking-tight">Settings</h1>
        <p className="text-[13px] text-[var(--color-text-muted)] mt-1">Manage your workspace preferences</p>
      </div>

      <Card variant="glass">
        <CardHeader>
          <CardTitle>Profile</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <Label>Full Name</Label>
              <Input defaultValue="Demo User" />
            </div>
            <div>
              <Label>Email</Label>
              <Input defaultValue="demo@leadforge.ai" type="email" />
            </div>
          </div>
          <Button leftIcon={<Save className="size-4" />}>Save Changes</Button>
        </CardContent>
      </Card>

      <Card variant="glass">
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Gemini API Key</Label>
            <Input type="password" placeholder="••••••••••" />
          </div>
          <div>
            <Label>SerpAPI Key</Label>
            <Input type="password" placeholder="••••••••••" />
          </div>
          <Button leftIcon={<Save className="size-4" />}>Save Keys</Button>
        </CardContent>
      </Card>
    </div>
  );
}
