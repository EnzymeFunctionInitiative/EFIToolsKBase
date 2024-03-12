#!/usr/bin/perl


{
    package Error;
    use strict;
    use warnings;

    use Exporter qw(import);
    our @EXPORT = qw(throw);


    sub throw {
        my $errorCode = shift;
        my @messages = @_;
        $! = $errorCode;
        die(join("\n", @messages) . "\n");
    }
}

####################################################################################################
# Subcommand
#
{
    package Command;
    use strict;
    use warnings;


    # Don't do validation in new; that happens in the validate sub after creation.
    sub new {
        my ($class, @args) = @_;
        my $self = {error_code => 0, error_message => ""};
        bless($self, $class);
        return $self;
    }

    # Validation occurs here
    # Returns error message if there was a problem, otherwise returns 0
    sub init {
        my $self = shift;
        return 0;
    }

    sub run {
        my $self = shift;
        return 0;
    }

    sub formatHelp {
        my @lines = @_;
        return join("\n", @lines);
    }

    sub getError {
        my $self = shift;
        return ($self->{error_code}, $self->{error_message});
    }
    sub setError {
        my $self = shift;
        $self->{error_code} = shift || 0;
        $self->{error_message} = shift || "";
    }
}


####################################################################################################
# EST Subcommand
#
{
    package EST;
    use strict;
    use warnings;
    use base 'Command';


    our $COMMAND = "EST";

    sub new {
        my ($class, @args) = @_;
        my $self = $class->SUPER::new(@args);
        return $self;
    }

    # Validation occurs here
    # Returns error message if there was a problem, otherwise returns 0
    sub init {
        my $self = shift;
        my @args = @_;

        if (@args == 0) {
            $self->setError(1, "Need subcommand for EST");
            return 0;
        }

        my $commandName = shift @args;
        my %commands = (
            "import" => sub { return $self->run_import(@args); },
            "blast-chunk" => sub {$self->run_blast_chunk(@args); },
            "mux" => sub { return $self->run_mux(@args); },
        );

        if (not $commands{$commandName}) {
            $self->setError(1, "Invalid EST subcommand $commandName");
            return 0;
        }

        $self->{command_name} = $commandName;
        $self->{command} = $commands{$commandName};
        $self->{args} = \@args;

        return 1;
    }

    sub run {
        my $self = shift;
        return $self->{command}->();
    }
    sub run_import {
        my $self = shift;
        my @args = @_;
        my $arg = shift @args || ($self->setError(2, "No args given to EST import") and return 0);
        print("EST importing from '$arg'\n");
        return 1;
    }
    sub run_blast_chunk {
        my $self = shift;
        my @args = @_;
        my $arg = shift @args || ($self->setError(2, "No args given to EST blast-chunk") and return 0);
        print("EST blast-chunking '$arg'\n");
        return 1;
    }
    sub run_mux {
        my $self = shift;
        my @args = @_;
        $self->setError(2, "No args given to EST mux") and return 0 if not @args;
        my $args = join(", ", @args);
        print("EST mux-ing $args\n");
        return 1;
    }

    sub getHelp {
        my $self = shift;
        my $help = "est <command> [args]";
        return Command::formatHelp($help);
    }
}


####################################################################################################
# GNT Subcommand
#
{
    package GNT;
    use strict;
    use warnings;
    use base 'Command';


    our $COMMAND = "GNT";

    sub new {
        my ($class, @args) = @_;
        my $self = $class->SUPER::new(@args);
        return $self;
    }

    # Validation occurs here
    sub init {
        my $self = shift;
        my @args = @_;

        if (@args == 0) {
            $self->setError(1, "Need subcommand for GNT");
            return 0;
        }

        my $commandName = shift @args;
        my $command = sub {};

        $self->{command_name} = $commandName;
        $self->{args} = \@args;

        return 1;
    }

    sub run {
        my $self = shift;
        my @args = @{$self->{args}};
        print("GNT $self->{command_name} " . join(" ", @args) . ")\n");
        return 0;
    }

    sub getHelp {
        my $self = shift;
        my $help = "gnt <command> [args]";
        return Command::formatHelp($help);
    }
}


####################################################################################################
# Route command data to proper command.
#
{
    package Router;
    use strict;
    use warnings;


    our $HELP_COMMAND = "HELP";

    sub new {
        my ($class, @args) = @_;
        my $subcommand = shift(@args); # Should be validated at this point.
        $subcommand = uc($subcommand);
        my $self = {};
        bless($self, $class);
        if ($subcommand eq $HELP_COMMAND) {
            if ($args[0]) {
                $subcommand = uc($args[0]);
            }
            $self->{is_help} = 1;
        } elsif ($args[0] and uc($args[0]) eq $HELP_COMMAND) {
            $self->{is_help} = 1;
        }
        $self->{subcommand} = getSubcommand($subcommand);
        $self->{args} = \@args;
        return $self;
    }

    # Creates a subcommand, and should only be called internally
    sub getSubcommand {
        my $subcommand = shift;
        if ($subcommand eq $HELP_COMMAND) {
            return $HELP_COMMAND;
        } elsif ($subcommand eq $EST::COMMAND) {
            return EST->new();
        } elsif ($subcommand eq $GNT::COMMAND) {
            return GNT->new();
        } else {
            die; # Should never get here, because command is validated in validateSubcommandName
        }
    }
    sub getSubcommandNames {
        return ($EST::COMMAND, $GNT::COMMAND);
    }

    # Validate the name only; doesn't create an object
    # This throws an error if things are not valid.
    sub validateSubcommandName {
        my $subcommandName = shift || Error::throw(99, "Invalid subcommand ''");
        my @args = @_;

        $subcommandName = uc($subcommandName);
        my %subcommands = map { $_ => 1 } getSubcommandNames();
        if ($subcommandName eq $HELP_COMMAND) {
            return 1;
        } elsif ($subcommands{$subcommandName}) {
            return 1;
        } else {
            #TODO: do we die here or elsewhere
            Error::throw(99, "Invalid subcommand '$subcommandName'");
        }
    }

    # Returns true if the action request is help
    sub isHelp {
        my $self = shift;
        return $self->{is_help};
    }

    # Validate inputs to the command and perform any necessary command initialization.
    # TODO: maybe need to rename this to validate_and_init or something
    sub validate {
        my $self = shift;
        return 1 if $self->{subcommand} eq $HELP_COMMAND;
        return $self->{subcommand}->init(@{$self->{args}});
    }

    # Return errors from subcommand
    sub getError {
        my $self = shift;
        return ($self->{subcommand}->getError());
    }

    # Display help; either subcommand help or system help
    sub help {
        my $self = shift;
        if (@{$self->{args}} > 0) {
            return $self->{subcommand}->getHelp(@{$self->{args}});
        } else {
            return Router::systemHelp();
        }
    }
    sub systemHelp {
        my @modules = map { lc($_) } Router::getSubcommandNames();
        my $mods = join("\n", map { sprintf("    %-15s execute %s", $_, $_) } @modules);
        return <<HELP;
Usage: $0 <command>
Commands:
$mods
HELP
    }

    # Returns the subcommand object
    sub create {
        my $self = shift;
        return $self->{subcommand};
    }
}


package main;
use strict;
use warnings;

use Getopt::Long qw(:config pass_through);


my $subcommandName = shift @ARGV || "help";

# throws an error if it's not valid
Router::validateSubcommandName($subcommandName);

# Find the subcommand type; this returns a function
my $router = Router->new($subcommandName, @ARGV);

# Display help
if ($router->isHelp()) {
    printHelp($router->help());
    exit(0);
}

# Validation
if (not $router->validate()) {
    Error::throw($router->getError());
}

# Create the subcommand object and any thing necessary, such as database connections
my $subcommand = $router->create();
# Run the subcommand
if (not $subcommand->run()) {
    Error::throw($router->getError());
}





sub printHelp {
    print(join("\n", @_), "\n");
}




1;
