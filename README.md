
📊 أداة فحص حالة التوظيف (Tawdif Status Checker)
أداة بايثون تلقائية لفحص حالة ملفات التوظيف بالتعاقد لعدة حسابات على منصة "توظيف" التابعة لوزارة التربية الوطنية الجزائرية، مع عرض النتائج بشكل احترافي ومنظم في الطرفية.

✨ المميزات الرئيسية
 * فحص تلقائي: يقوم بفحص قائمة من الحسابات بشكل آلي من ملف accounts.txt.
 * واجهة احترافية: يستخدم مكتبة rich لعرض النتائج في لوحات ملونة ومنظمة.
 * شريط تقدم ديناميكي: يعرض شريط تقدم مباشر لمتابعة عملية فحص الحسابات.
 * لوحة إحصائيات: يقدم ملخصًا نهائيًا لعدد الحالات (مطابق، قيد الدراسة، مرفوض...).
 * دعم كامل للعربية: يعالج ويعرض اللغة العربية بشكل سليم تمامًا في الطرفيات مثل Termux.

 * جهز ملف الحسابات:
   * قم بإنشاء ملف باسم accounts.txt.
   * أضف حساباتك، كل حساب في سطر، بالتنسيق التالي: username:password.
🚀 التشغيل
لتشغيل الأداة، نفذ الأمر التالي في الطرفية:
python t.py

📊 Tawdif Status Checker
An automation Python script to check the status of multiple contractual teaching applications on the "Tawdif" platform of the Algerian Ministry of National Education, featuring a professional and organized display in the terminal.
✨ Key Features
 * Automated Checking: Automatically checks a list of accounts from an accounts.txt file.
 * Professional UI: Uses the rich library to display results in colorful, organized panels.
 * Dynamic Progress Bar: Shows a live progress bar to track the account checking process.
 * Statistics Dashboard: Provides a final summary of all statuses (Accepted, Pending, Rejected, etc.).
 * Full Arabic Support: Correctly processes and renders the Arabic language in terminals like Termux.


 * Install the required libraries:
   pip install -r requirements.txt

 * Prepare the accounts file:
   * Create a file named accounts.txt.
   * Add your accounts, one per line, in the following format: username:password.
🚀 Usage
To run the script, execute the following command in your terminal:
python t.py

