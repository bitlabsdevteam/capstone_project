"use client"

import * as React from "react"
import { cn } from "@/lib/utils"

interface ScrollAreaProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "vertical" | "horizontal" | "both"
}

const ScrollArea = React.forwardRef<HTMLDivElement, ScrollAreaProps>(
  ({ className, children, orientation = "vertical", ...props }, ref) => {
    const getScrollbarClasses = () => {
      switch (orientation) {
        case "horizontal":
          return "overflow-x-auto overflow-y-hidden"
        case "both":
          return "overflow-auto"
        default:
          return "overflow-y-auto overflow-x-hidden"
      }
    }

    return (
      <div
        ref={ref}
        className={cn(
          "relative",
          getScrollbarClasses(),
          "scrollbar-thin scrollbar-track-transparent scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 hover:scrollbar-thumb-gray-400 dark:hover:scrollbar-thumb-gray-500",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }
)
ScrollArea.displayName = "ScrollArea"

export { ScrollArea }