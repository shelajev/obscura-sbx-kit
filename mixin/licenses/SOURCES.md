# Notice sources

These are license texts, not vendored implementation. The archive contains only
`obscura` and `obscura-worker`; it supplies no consolidated third-party notice.

- Obscura source: h4ckf0r0day/obscura v0.2.6, commit
  8534b401898ed17b62f69bdc3d5eb186bffb0d60; root Apache license.
  cosmic-text, taffy, wreq-util and Noto Color Emoji notices copied from that tree.
- rusty_v8: Cargo.lock version 150.4.0; MIT license from
  https://github.com/denoland/rusty_v8/blob/v150.4.0/LICENSE
- V8: rusty_v8 v150.4.0's v8 submodule ac1e23989121713ca642f6650b34deff7b686896;
  https://github.com/denoland/v8/blob/ac1e23989121713ca642f6650b34deff7b686896/LICENSE
- Liberation fonts: https://github.com/liberationfonts/liberation-fonts/blob/2.1.5/LICENSE
- DejaVu fonts: https://github.com/dejavu-fonts/dejavu-fonts/blob/version_2_37/LICENSE

The font source release pin identifies the license text; it does not assert the
embedded upstream font binaries were independently rebuilt. Container-base
notices remain supplied by their publishers. Recheck this inventory on upgrades;
do not represent it as a complete upstream binary SBOM.
