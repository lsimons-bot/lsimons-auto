on run
  set promptText to the clipboard as string

  tell application "Microsoft 365 Copilot" to activate

  delay 0.2

  tell application "System Events"
    set copilotProc to missing value
    set copilotProc to first process whose name is "Microsoft 365 Copilot"

    if copilotProc is missing value then
      display dialog "Could not find a running Copilot process. Is Microsoft 365 Copilot installed and allowed in Accessibility?" buttons {"OK"} default button 1
      return
    end if

    set frontmost of copilotProc to true

    set winList to windows of copilotProc
    if (count of winList) is 0 then
      delay 0.2
      set winList to windows of copilotProc
      if (count of winList) is 0 then
        display dialog "Could not find a running Copilot window. Is Microsoft 365 Copilot installed and allowed in Accessibility?" buttons {"OK"} default button 1
        return
      end if
    end if
    set theWin to item 1 of winList

    -- ------- Helpers (AX targeting) -------
    script AXHelpers
      -- Try focusing by common name/label
      on tryFocusByName(targetWin, nameList)
        repeat with nm in nameList
          try
            set tf to (first text field of targetWin whose name contains nm)
            perform action "AXPress" of tf
            return true
          end try
          try
            set ta to (first text area of targetWin whose name contains nm)
            perform action "AXPress" of ta
            return true
          end try
        end repeat
        return false
      end tryFocusByName

      -- Try direct roles on the window
      on tryDirectRoles(targetWin)
        try
          set tf to first text field of targetWin
          perform action "AXPress" of tf
          return true
        end try
        try
          set ta to first text area of targetWin
          perform action "AXPress" of ta
          return true
        end try
        return false
      end tryDirectRoles

      -- Try groups and scroll areas
      on tryGroupsAndScrollAreas(targetWin)
        try
          set grp to first group of targetWin
          try
            set tf2 to first text field of grp
            perform action "AXPress" of tf2
            return true
          end try
          try
            set ta2 to first text area of grp
            perform action "AXPress" of ta2
            return true
          end try
        end try

        try
          set sc to first scroll area of targetWin
          try
            set tf3 to first text field of sc
            perform action "AXPress" of tf3
            return true
          end try
          try
            set ta3 to first text area of sc
            perform action "AXPress" of ta3
            return true
          end try
        end try

        return false
      end tryGroupsAndScrollAreas

      -- Try inside WebView: filter UI elements with AX role "AXWebArea" (or role description "web area")
      on tryWebAreas(targetWin)
        try
          -- Find all UI elements which are AXWebArea or have role description "web area"
          set uiElems to every UI element of targetWin
          repeat with e in uiElems
            set r to ""
            set roleDesc to ""
            try
              set r to role of e
            end try
            try
              set roleDesc to role description of e
            end try
            if (r is "AXWebArea") or (roleDesc contains "web area") then
              -- Search text fields/areas under this web area
              try
                set wtf to first text field of e
                perform action "AXPress" of wtf
                return true
              end try
              try
                set wta to first text area of e
                perform action "AXPress" of wta
                return true
              end try
            end if
          end repeat
        end try
        return false
      end tryWebAreas
    end script
    -- ------- End helpers -------

    -- Candidate names we've seen across builds
    set candidateNames to {"Type a message", "Type your message", "Ask Copilot", "Prompt", "Message", "Ask me anything", "Chat input"}

    set focusedOK to AXHelpers's tryFocusByName(theWin, candidateNames)
    if focusedOK is false then
      set focusedOK to AXHelpers's tryDirectRoles(theWin)
    end if
    if focusedOK is false then
      set focusedOK to AXHelpers's tryGroupsAndScrollAreas(theWin)
    end if
    if focusedOK is false then
      set focusedOK to AXHelpers's tryWebAreas(theWin)
    end if

    set the clipboard to promptText
    if focusedOK then
      keystroke "a" using {command down}
      delay 0.05
      keystroke "v" using {command down}
    else
      -- Fallback: paste to current focus
      keystroke "v" using {command down}
    end if
  end tell
end run
