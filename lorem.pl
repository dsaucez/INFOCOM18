#!/usr/bin/env perl

use Text::Lorem;

my $text = Text::Lorem->new();
$paragraphs = $text->paragraphs($ARGV[0]);

print $paragraphs;
