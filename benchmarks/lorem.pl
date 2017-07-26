#!/usr/bin/env perl

use Text::Lorem;

# make sure we generate always the same
srand($ARGV[1]);

my $text = Text::Lorem->new();
$paragraphs = $text->paragraphs($ARGV[0]);

print $paragraphs;
