"use client"

import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { HelpCircle } from "lucide-react"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <>
            <AppSidebar />
            <SidebarInset className="bg-background/50 backdrop-blur-sm">
                <header className="flex h-16 shrink-0 items-center gap-2 transition-[width,height] ease-linear group-has-[[data-collapsible=icon]]/sidebar-wrapper:h-12 border-b border-border/40 px-4">
                    <SidebarTrigger />
                    <Separator orientation="vertical" className="mr-2 h-4" />
                    <div className="flex items-center gap-2 px-2">
                        <span className="text-sm font-medium text-muted-foreground">NeuroSupply</span>
                        <span className="text-sm text-muted-foreground/40">/</span>
                        <span className="text-sm font-semibold">Dashboard</span>
                    </div>
                    <div className="ml-auto flex items-center gap-4">
                        <Button 
                            variant="outline" 
                            size="sm" 
                            className="bg-primary/5 hover:bg-primary/10 border-primary/20 text-primary gap-2 hidden sm:flex"
                            onClick={() => window.open('https://neuro-supply.com/guide', '_blank')}
                        >
                            <HelpCircle className="h-4 w-4" />
                            Гайд / Hướng dẫn
                        </Button>
                    </div>
                </header>
                <main className="flex-1 overflow-auto p-6 md:p-8 lg:p-10">
                    <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
                        {children}
                    </div>
                </main>
            </SidebarInset>
        </>
    )
}
