; ============================================================================
; DRAGON BALL Z: BUU'S FURY - LEGACY OF GOKU 4 ULTIMATE EDITION
; Tutorial System - Contextual Help for New Mechanics
; Phase 117: Final Polish to 10/10
; Language: English
; ============================================================================

; -----------------------------------------------------------------------------
; Constants
; -----------------------------------------------------------------------------

; Tutorial flags (1 bit per tutorial)
TUTORIAL_EQUIPMENT   equ 0
TUTORIAL_FUSION      equ 1
TUTORIAL_QUESTS      equ 2
TUTORIAL_LSSJ        equ 3
TUTORIAL_HIDDEN_ITEMS equ 4

; -----------------------------------------------------------------------------
; Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "Tutorial System Variables", WRAM

wTutorialFlags:: ds 1  ; Bit field for which tutorials have been shown

ENDS

; -----------------------------------------------------------------------------
; Tutorial Text Pointers
; -----------------------------------------------------------------------------

SECTION "Tutorial Text", ROM0

; Equipment Tutorial
EquipmentTutorialText::
    db "Press A to equip", $0A
    db "weapons and armor.", $0A
    db "Each piece affects", $0A
    db "your stats:", $0A
    db "", $0A
    db "+ATK: Increases", $0A
    db "    damage dealt", $0A
    db "+DEF: Reduces", $0A
    db "    damage taken", $0A
    db "+SPD: Increases", $0A
    db "    speed", $FF

; Fusion Tutorial
FusionTutorialText::
    db "To fuse, talk to", $0A
    db "Elder Kai in the", $0A
    db "Fusion Arena.", $0A
    db "", $0A
    db "You need 2", $0A
    db "compatible", $0A
    db "characters.", $0A
    db "", $0A
    db "Fusion lasts for", $0A
    db "a limited time!", $FF

; Quests Tutorial
QuestsTutorialText::
    db "Side quests give", $0A
    db "unique rewards.", $0A
    db "", $0A
    db "Check your quest", $0A
    db "log (START button)", $0A
    db "to see objectives.", $FF

; LSSJ Tutorial
LSSJTutorialText::
    db "Legendary Super", $0A
    db "Saiyan is a", $0A
    db "powerful form!", $0A
    db "", $0A
    db "It has a time", $0A
    db "limit, so use it", $0A
    db "wisely!", $FF

; Hidden Items Tutorial
HiddenItemsTutorialText::
    db "Some items are", $0A
    db "hidden! Use the", $0A
    db "Scanner ability", $0A
    db "to find them.", $0A
    db "", $0A
    db "Look for visual", $0A
    db "clues in the", $0A
    db "environment.", $FF

; -----------------------------------------------------------------------------
; Tutorial Text Pointer Table
; -----------------------------------------------------------------------------

TutorialTextPointers::
    dw EquipmentTutorialText   ; 0
    dw FusionTutorialText      ; 1
    dw QuestsTutorialText      ; 2
    dw LSSJTutorialText        ; 3
    dw HiddenItemsTutorialText ; 4

; -----------------------------------------------------------------------------
; ShowTutorialIfNeeded
; Input: a = tutorial ID
; -----------------------------------------------------------------------------

ShowTutorialIfNeeded::
    push af
    push hl
    push bc

    ; Check if tutorial has already been shown
    ld b, a
    ld a, [wTutorialFlags]
    and (1 << b)
    jr nz, .already_shown

    ; Get text pointer
    ld hl, TutorialTextPointers
    sla b
    ld c, b
    add hl, bc
    ld a, [hli]
    ld h, [hl]
    ld l, a

    ; Show text box
    call ShowTextBox
    call PrintText

    ; Mark as shown
    ld a, [wTutorialFlags]
    or (1 << b)
    ld [wTutorialFlags], a

.already_shown:
    pop bc
    pop hl
    pop af
    ret

; -----------------------------------------------------------------------------
; CheckAndShowTutorial
; Checks if a tutorial should be shown based on game state
; -----------------------------------------------------------------------------

CheckAndShowTutorial::
    ; Check equipment tutorial (first time opening equipment menu)
    ld a, [wEquipmentMenuOpened]
    and a
    jr nz, .check_fusion
    ld a, TUTORIAL_EQUIPMENT
    call ShowTutorialIfNeeded
    ld a, 1
    ld [wEquipmentMenuOpened], a

.check_fusion:
    ; Check fusion tutorial (first time entering Fusion Arena)
    ld a, [wInFusionArena]
    and a
    jr z, .check_quests
    ld a, [wFusionTutorialShown]
    and a
    jr nz, .check_quests
    ld a, TUTORIAL_FUSION
    call ShowTutorialIfNeeded
    ld a, 1
    ld [wFusionTutorialShown], a

.check_quests:
    ; Check quests tutorial (first time accepting a quest)
    ld a, [wFirstQuestAccepted]
    and a
    jr z, .check_lssj
    ld a, [wQuestsTutorialShown]
    and a
    jr nz, .check_lssj
    ld a, TUTORIAL_QUESTS
    call ShowTutorialIfNeeded
    ld a, 1
    ld [wQuestsTutorialShown], a

.check_lssj:
    ; Check LSSJ tutorial (first time transforming)
    ld a, [wFirstLSSJTransform]
    and a
    jr z, .done
    ld a, [wLSSJTutorialShown]
    and a
    jr nz, .done
    ld a, TUTORIAL_LSSJ
    call ShowTutorialIfNeeded
    ld a, 1
    ld [wLSSJTutorialShown], a

.done:
    ret

; -----------------------------------------------------------------------------
; Hook into Equipment Menu
; -----------------------------------------------------------------------------

OpenEquipmentMenu::
    ; Show tutorial if needed
    ld a, TUTORIAL_EQUIPMENT
    call ShowTutorialIfNeeded

    ; Original equipment menu code
    call DrawEquipmentMenu
    ret

; -----------------------------------------------------------------------------
; Hook into Fusion Arena Entry
; -----------------------------------------------------------------------------

EnterFusionArena::
    ; Set flag that we're in Fusion Arena
    ld a, 1
    ld [wInFusionArena], a

    ; Show tutorial if needed
    ld a, TUTORIAL_FUSION
    call ShowTutorialIfNeeded

    ; Original entry code
    call LoadFusionArenaMap
    ret

; -----------------------------------------------------------------------------
; Hook into Quest Acceptance
; -----------------------------------------------------------------------------

AcceptQuest::
    ; Set flag that first quest was accepted
    ld a, [wFirstQuestAccepted]
    and a
    jr nz, .skip_first_quest_flag
    ld a, 1
    ld [wFirstQuestAccepted], a

.skip_first_quest_flag:
    ; Show tutorial if needed
    ld a, TUTORIAL_QUESTS
    call ShowTutorialIfNeeded

    ; Original quest acceptance code
    call AddQuestToLog
    ret

; -----------------------------------------------------------------------------
; Hook into LSSJ Transformation
; -----------------------------------------------------------------------------

TransformToLSSJ::
    ; Set flag that first LSSJ transform happened
    ld a, [wFirstLSSJTransform]
    and a
    jr nz, .skip_first_lssj_flag
    ld a, 1
    ld [wFirstLSSJTransform], a

.skip_first_lssj_flag:
    ; Show tutorial if needed
    ld a, TUTORIAL_LSSJ
    call ShowTutorialIfNeeded

    ; Original transformation code
    call ApplyLSSJStats
    ret

; -----------------------------------------------------------------------------
; Additional Variables (in WRAM)
; -----------------------------------------------------------------------------

SECTION "Tutorial System Additional Variables", WRAM

wEquipmentMenuOpened:: ds 1
wInFusionArena:: ds 1
wFusionTutorialShown:: ds 1
wFirstQuestAccepted:: ds 1
wQuestsTutorialShown:: ds 1
wFirstLSSJTransform:: ds 1
wLSSJTutorialShown:: ds 1
wHiddenItemsTutorialShown:: ds 1

ENDS
