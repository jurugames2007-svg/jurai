#---------------------------------------------------------------------------------
# Dragon Ball Z: Buu's Fury - libgba / devkitARM starter project
#---------------------------------------------------------------------------------
.SUFFIXES:

ifeq ($(strip $(DEVKITARM)),)
$(error "DEVKITARM no esta definido. Instala devkitPro y exporta DEVKITARM")
endif

include $(DEVKITARM)/gba_rules

# gba_rules expects the ARM compiler and the devkitPro utilities on PATH. This
# also makes `make` work in a fresh shell after DEVKITARM is exported.
export PATH := $(DEVKITARM)/bin:$(DEVKITPRO)/tools/bin:$(PATH)

#---------------------------------------------------------------------------------
# Project layout
#---------------------------------------------------------------------------------
TARGET      := $(notdir $(CURDIR))
BUILD       := build
SOURCES     := source
INCLUDES    := include
DATA        :=
MUSIC       :=

#---------------------------------------------------------------------------------
# ARM7TDMI / GBA compiler options
#---------------------------------------------------------------------------------
ARCH       := -mthumb -mthumb-interwork
CFLAGS     := -g -Wall -Wextra -O2 \
              -mcpu=arm7tdmi -mtune=arm7tdmi \
              -ffunction-sections -fdata-sections \
              $(ARCH)
CFLAGS     += $(INCLUDE)
CXXFLAGS   := $(CFLAGS) -fno-rtti -fno-exceptions
ASFLAGS    := -g $(ARCH)
LDFLAGS    := -g $(ARCH) -Wl,--gc-sections -Wl,-Map,$(notdir $@).map

# libgba is intentionally linked explicitly; this is the library used by main.c.
LIBS      := -lgba
LIBDIRS   := $(LIBGBA)

#---------------------------------------------------------------------------------
# Everything below is the standard devkitPro gba_rules wiring.
#---------------------------------------------------------------------------------
ifneq ($(BUILD),$(notdir $(CURDIR)))

.DEFAULT_GOAL := $(BUILD)

export OUTPUT    := $(CURDIR)/$(TARGET)
export VPATH     := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) \
                    $(foreach dir,$(DATA),$(CURDIR)/$(dir))
export DEPSDIR   := $(CURDIR)/$(BUILD)

CFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES    := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
BINFILES    := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

export OFILES_BIN     := $(addsuffix .o,$(BINFILES))
export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES         := $(OFILES_BIN) $(OFILES_SOURCES)
export HFILES         := $(addsuffix .h,$(subst .,_,$(BINFILES)))

export INCLUDE  := $(foreach dir,$(INCLUDES),-iquote $(CURDIR)/$(dir)) \
                   $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                   -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

# Link through the compiler driver so gba.specs supplies the correct GBA
# startup code, linker script and libraries.
ifeq ($(strip $(CPPFILES)),)
export LD := $(CC)
else
export LD := $(CXX)
endif

.PHONY: $(BUILD) clean all

clean:
	@echo clean ...
	@rm -rf $(BUILD) $(OUTPUT).elf $(OUTPUT).gba $(OUTPUT).elf.map

$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

else

.DEFAULT_GOAL := all

DEPENDS := $(OFILES:.o=.d)

#---------------------------------------------------------------------------------
# Main targets
#---------------------------------------------------------------------------------
all: $(OUTPUT).gba

$(OUTPUT).gba: $(OUTPUT).elf

$(OUTPUT).elf: $(OFILES)
	@echo linking $(notdir $@)
	@$(LD) -specs=gba.specs $(LDFLAGS) $(OFILES) $(LIBPATHS) $(LIBS) -o $@

#---------------------------------------------------------------------------------
# C/C++/assembly compilation
#---------------------------------------------------------------------------------
%.o: %.c
	@echo $(notdir $<)
	@$(CC) -MMD -MP -MF $*.d $(CFLAGS) -c $< -o $@

%.o: %.cpp
	@echo $(notdir $<)
	@$(CXX) -MMD -MP -MF $*.d $(CXXFLAGS) -c $< -o $@

%.o: %.s
	@echo $(notdir $<)
	@$(CC) -MMD -MP -MF $*.d $(ASFLAGS) -c $< -o $@

-include $(DEPENDS)

clean:
	@echo clean ...
	@rm -rf $(BUILD) $(OUTPUT).elf $(OUTPUT).gba $(OUTPUT).elf.map

endif
