import { Topbar } from "@/components/shell/topbar";
import { SettingsForm } from "@/components/settings/settings-form";

export const dynamic = "force-dynamic";

export default function SettingsPage() {
  return (
    <>
      <Topbar
        title="Inställningar"
        description="Din firma, din persona, dina integrationer"
      />
      <div className="flex-1 overflow-y-auto bg-linne">
        <div className="mx-auto max-w-3xl px-8 lg:px-12 py-10">
          <SettingsForm />
        </div>
      </div>
    </>
  );
}
