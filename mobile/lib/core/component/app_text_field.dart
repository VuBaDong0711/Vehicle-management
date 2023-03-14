import 'package:flutter/material.dart';

class AppTextFields extends StatelessWidget {
  const AppTextFields({
    Key? key,
    this.controller,
    this.hint,
    this.keyboardType,
    this.obscureText = false,
    this.prefix,
    this.suffix,
    this.textInputAction,
  }): super(key: key);

  final TextEditingController? controller;
  final TextInputType? keyboardType;
  final TextInputAction? textInputAction;
  final bool obscureText;
  final Widget? prefix;
  final Widget? suffix;
  final String? hint;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.max,
      crossAxisAlignment: CrossAxisAlignment.center,
      mainAxisAlignment: MainAxisAlignment.start,
      children: [
        if(prefix != null) ...[
          prefix!,
          const SizedBox(width: 10,)
        ],
        Expanded(child: TextField(
          controller: controller,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          obscureText: obscureText,
          decoration: InputDecoration(
            suffixIcon: suffix,
            hintText: hint,
            hintStyle: Theme.of(context).textTheme.bodyLarge?.copyWith(color: Colors.grey)
          ),
        ))
      ],
    );
  }
}